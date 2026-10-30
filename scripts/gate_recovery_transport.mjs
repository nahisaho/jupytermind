import { createHash, randomUUID } from 'node:crypto';
import { lstat, mkdir, open, readFile, realpath, rename, rm } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, isAbsolute, relative, resolve, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const protectedPaths = [
  '.musubix/evidence/order.json',
  '.musubix/evidence/tdd.json',
  '.musubix/evidence/changes.json',
];
const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');
const equal = (left, right) => JSON.stringify(left) === JSON.stringify(right);

function validateManifest(manifest) {
  const hash = (value) => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
  if (manifest.schemaVersion !== 1 || !['planned', 'applying', 'completed'].includes(manifest.state)) {
    throw new Error('Invalid transport manifest state');
  }
  if (!Array.isArray(manifest.files) || new Set(manifest.files.map((item) => item.path)).size
      !== manifest.files.length || protectedPaths.some((path) =>
    !manifest.files.some((item) => item.path === path))) throw new Error('Invalid artifact manifest');
  for (const item of manifest.files) {
    const report = typeof item.path === 'string'
      && item.path.startsWith('.musubix/evidence/native/recovery/');
    if ((!protectedPaths.includes(item.path) && !report)
        || !hash(item.afterSha256)
        || (item.beforeSha256 !== null && !hash(item.beforeSha256))
        || (report && item.beforeSha256 !== null)) throw new Error('Unapproved artifact manifest');
  }
  if (!Array.isArray(manifest.inputFiles) || !manifest.inputFiles.length
      || new Set(manifest.inputFiles.map((item) => item.path)).size !== manifest.inputFiles.length
      || manifest.inputFiles.some((item) => typeof item.path !== 'string'
        || item.path.startsWith('.musubix/evidence/') || !hash(item.sha256))) {
    throw new Error('Invalid input manifest');
  }
  if (!Array.isArray(manifest.completedPaths) || manifest.completedPaths.some((path) =>
    !manifest.files.some((item) => item.path === path))) throw new Error('Invalid artifact progress');
}

async function bytes(path) {
  try {
    return await readFile(path);
  } catch (error) {
    if (error.code === 'ENOENT') return null;
    throw error;
  }
}

async function checkedPath(root, name) {
  if (typeof name !== 'string' || !name || isAbsolute(name)
      || name.split(/[\\/]/).some((part) => !part || part === '.' || part === '..')) {
    throw new Error(`Unsafe artifact/input path: ${name}`);
  }
  const path = resolve(root, name);
  if (relative(root, path).startsWith(`..${sep}`)) throw new Error('Path escapes root');
  let cursor = root;
  for (const part of relative(root, path).split(sep)) {
    cursor = resolve(cursor, part);
    try {
      if ((await lstat(cursor)).isSymbolicLink()) throw new Error('Symlink path rejected');
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
  }
  return path;
}

async function atomicWrite(path, content) {
  await mkdir(dirname(path), { recursive: true });
  const temporary = `${path}.${randomUUID()}.tmp`;
  try {
    const handle = await open(temporary, 'wx');
    try {
      await handle.writeFile(content);
      await handle.sync();
    } finally {
      await handle.close();
    }
    await rename(temporary, path);
    const directory = await open(dirname(path), 'r');
    try {
      await directory.sync();
    } finally {
      await directory.close();
    }
  } finally {
    await rm(temporary, { force: true });
  }
}

async function save(path, manifest) {
  await atomicWrite(path, `${JSON.stringify(manifest, null, 2)}\n`);
}

async function nativeModule(packagePath) {
  const canonical = await realpath(packagePath);
  const packageInfo = JSON.parse(await readFile(canonical, 'utf8'));
  if (packageInfo.name !== 'musubix3' || packageInfo.version !== '0.1.22') {
    throw new Error('Expected the installed musubix3 0.1.22 package');
  }
  const entry = createRequire(canonical).resolve('musubix3/analysis');
  return { packagePath: canonical, version: packageInfo.version, entry, sha256: sha(await readFile(entry)) };
}

function preservedChanges(original, current) {
  if (current.length < original.length) return false;
  return original.every((record, index) => {
    const successor = current[index];
    return Object.entries(record).every(([key, value]) => {
      if (key === 'phases') {
        return Object.entries(value).every(([phase, payload]) =>
          equal(successor.phases?.[phase], payload)
          || (phase === 'quality' && successor.qualityHistory?.some((old) => equal(old, payload))));
      }
      if (key === 'qualityHistory') return equal(successor[key]?.slice(0, value.length), value);
      return equal(successor[key], value);
    });
  });
}

async function prefix(beforeRoot, afterRoot) {
  const sides = [];
  for (const root of [beforeRoot, afterRoot]) {
    const documents = {};
    for (const name of protectedPaths) {
      const document = JSON.parse(await readFile(await checkedPath(root, name), 'utf8'));
      const expectedSchema = name.endsWith('/changes.json') ? 2 : 1;
      if (document.schemaVersion !== expectedSchema) throw new Error('Unsupported evidence schema');
      documents[name.split('/').at(-1)] = document;
    }
    sides.push(documents);
  }
  for (const [file, key] of [['order.json', 'records'], ['tdd.json', 'cycles'], ['tdd.json', 'chain']]) {
    const original = sides[0][file][key];
    const current = sides[1][file][key];
    if (!Array.isArray(original) || !Array.isArray(current)
        || !equal(original, current.slice(0, original.length))) {
      throw new Error(`Original ${file}/${key} prefix not preserved`);
    }
  }
  if (!preservedChanges(sides[0]['changes.json'].changes, sides[1]['changes.json'].changes)) {
    throw new Error('Original change prefix/payload not preserved');
  }
  return sides.map((side) => Object.fromEntries(
    [['order', side['order.json'].records], ['tdd', side['tdd.json'].chain]].map(([name, records]) =>
      [name, records.length
        ? { head: records.at(-1).recordSha256, sequence: records.at(-1).sequence }
        : { head: null, sequence: 0 }]),
  ));
}

async function inputs(manifest) {
  for (const item of manifest.inputFiles) {
    for (const root of [manifest.root, manifest.incomingRoot]) {
      const content = await bytes(await checkedPath(root, item.path));
      if (content === null || sha(content) !== item.sha256) throw new Error(`Input drift: ${item.path}`);
    }
  }
}

async function incomingFiles(manifest) {
  const contents = [];
  for (const item of manifest.files) {
    const content = await bytes(await checkedPath(manifest.incomingRoot, item.path));
    if (content === null || sha(content) !== item.afterSha256) {
      throw new Error(`Incoming artifact drift: ${item.path}`);
    }
    contents.push(content);
  }
  return contents;
}

/** @id CODE-GATE-RECOVERY-004
 * @implements REQ-GATE-RECOVERY-001
 * @design DES-GATE-RECOVERY-001
 */
export async function planTransport(input) {
  const root = await realpath(input.root);
  const incomingRoot = await realpath(input.incomingRoot);
  if (root === incomingRoot || root.startsWith(`${incomingRoot}${sep}`)
      || incomingRoot.startsWith(`${root}${sep}`)) throw new Error('Roots must be separate');
  if (!Array.isArray(input.files) || new Set(input.files).size !== input.files.length
      || protectedPaths.some((path) => !input.files.includes(path))) {
    throw new Error('All unique protected artifacts are required');
  }
  if (!Array.isArray(input.inputFiles) || !input.inputFiles.length
      || new Set(input.inputFiles).size !== input.inputFiles.length) throw new Error('Missing/duplicate inputs');
  const inputFiles = [];
  for (const path of input.inputFiles) {
    if (path.startsWith('.musubix/evidence/')) throw new Error('Evidence is not a fixed input');
    const content = await bytes(await checkedPath(root, path));
    if (content === null) throw new Error(`Missing input: ${path}`);
    inputFiles.push({ path, sha256: sha(content) });
  }
  const files = [];
  for (const path of input.files) {
    if (!protectedPaths.includes(path) && !path.startsWith('.musubix/evidence/native/recovery/')) {
      throw new Error(`Unapproved artifact: ${path}`);
    }
    const before = await bytes(await checkedPath(root, path));
    const after = await bytes(await checkedPath(incomingRoot, path));
    if (after === null || (!protectedPaths.includes(path) && before !== null)) {
      throw new Error(`Missing or previously existing report artifact: ${path}`);
    }
    files.push({ path, beforeSha256: before === null ? null : sha(before), afterSha256: sha(after) });
  }
  const [before, after] = await prefix(root, incomingRoot);
  const manifest = {
    schemaVersion: 1, transactionId: randomUUID(), root, incomingRoot, state: 'planned',
    nativeModule: await nativeModule(input.nativePackage), inputFiles, files,
    before, after, completedPaths: [],
  };
  validateManifest(manifest);
  await inputs(manifest);
  return manifest;
}

async function transact(manifestPath, recover, hooks) {
  const manifest = JSON.parse(await readFile(manifestPath, 'utf8'));
  validateManifest(manifest);
  if (!equal(await nativeModule(manifest.nativeModule.packagePath), manifest.nativeModule)) {
    throw new Error('Native module drift');
  }
  if (await realpath(manifest.root) !== manifest.root
      || await realpath(manifest.incomingRoot) !== manifest.incomingRoot) throw new Error('Root drift');
  const native = await import(pathToFileURL(manifest.nativeModule.entry));
  return native.withEvidenceWriterLock(manifest.root, 'gate-recovery-transport', async () => {
    await inputs(manifest);
    const contents = await incomingFiles(manifest);
    if (manifest.state === 'completed') {
      await prefix(manifest.incomingRoot, manifest.root);
      for (const item of manifest.files.filter((item) => !protectedPaths.includes(item.path))) {
        const content = await bytes(await checkedPath(manifest.root, item.path));
        if (content === null || sha(content) !== item.afterSha256) {
          throw new Error(`Immutable report artifact drift: ${item.path}`);
        }
      }
    } else {
      if (!recover && manifest.state !== 'planned') throw new Error('Recovery is required');
      for (const item of manifest.files) {
        const content = await bytes(await checkedPath(manifest.root, item.path));
        const actual = content === null ? null : sha(content);
        if (actual !== item.beforeSha256 && (!recover || actual !== item.afterSha256)) {
          throw new Error(`Unknown current artifact hash: ${item.path}`);
        }
      }
      manifest.state = 'applying';
      await save(manifestPath, manifest);
      for (const [index, item] of manifest.files.entries()) {
        const path = await checkedPath(manifest.root, item.path);
        const content = await bytes(path);
        const actual = content === null ? null : sha(content);
        if (actual !== item.beforeSha256 && actual !== item.afterSha256) {
          throw new Error(`Unknown current artifact hash: ${item.path}`);
        }
        if (actual !== item.afterSha256) {
          await atomicWrite(path, contents[index]);
          await hooks.afterRename?.(item.path);
        }
        if (!manifest.completedPaths.includes(item.path)) manifest.completedPaths.push(item.path);
        await save(manifestPath, manifest);
        await hooks.afterProgress?.(item.path);
      }
      await inputs(manifest);
      for (const item of manifest.files) {
        if (sha(await readFile(await checkedPath(manifest.root, item.path))) !== item.afterSha256) {
          throw new Error('Transport output mismatch');
        }
      }
      manifest.state = 'completed';
      await save(manifestPath, manifest);
    }
    return {
      state: 'completed', inputsVerified: true, prefixVerified: true,
      transactionId: manifest.transactionId, manifestSha256: sha(await readFile(manifestPath)),
    };
  });
}

export async function applyTransport(manifestPath, hooks = {}) {
  return transact(manifestPath, false, hooks);
}

export async function recoverTransport(manifestPath, hooks = {}) {
  return transact(manifestPath, true, hooks);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [operation, input, output] = process.argv.slice(2);
  let result;
  if (operation === 'plan') {
    result = await planTransport(JSON.parse(await readFile(input, 'utf8')));
    const destination = resolve(output);
    if ([result.root, result.incomingRoot].some((root) =>
      destination === root || destination.startsWith(`${root}${sep}`))) {
      throw new Error('Manifest must be outside both roots');
    }
    if (await bytes(destination) !== null) throw new Error('Manifest already exists');
    await save(destination, result);
  } else if (operation === 'apply') {
    result = await applyTransport(resolve(input));
  } else if (operation === 'recover') {
    result = await recoverTransport(resolve(input));
  } else {
    throw new Error('Expected plan, apply or recover');
  }
  console.log(JSON.stringify(result));
}
