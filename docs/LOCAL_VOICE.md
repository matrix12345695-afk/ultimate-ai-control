# Offline speech candidate (stage10 remains in progress)

This increment installs an acceptance-only native speech runtime in UAC's private tools
and adds `/voice4`, `/test_voice4` and the «🎙 Голос 4.0» menu. It does not yet receive or
transcribe the owner's Telegram messages, create tasks from speech or enable a paid API.
The next gate is private bounded audio ingestion, transcript preview, exact project selection
and explicit confirmation before enqueueing ordinary text. Recognized slash commands must
never become dispatcher commands. RU/UZ quality and actual owner recordings remain untested.

## Selected components and review

whisper.cpp v1.8.2 commit4979e04f5dcaccb36057e059bbaed8a2f5288315 (MIT), vendored
GGML/miniaudio/STB components and tiny multilingual Q5_1 model32,152,673 bytes are pinned
by source archive, model revision and SHA256 in voice_assets_contract.json. The model's
MIT license is declared by its public repository; model weights originate from OpenAI
Whisper. No third-party autonomous agent, plugin, tools or secret access is installed.
Public upstream advisory list was read and empty at review time; this does not establish
absence of vulnerabilities. Only the command-line target is built; server, curl, GPU,
OpenMP, BLAS and host-specific SIMD are disabled. Build uses one CPU/lowered priority,
one make job,1.5GiB address-space limit and bounded compiler time, with no global packages.
CMake3.31.6 portable wheel SHA is matched to PyPI release metadata; it is build-only.

Ubuntu Opus decoder and libraries are extracted from four exact hash-pinned Debian packages
without running package scripts or modifying system packages. Only opusdec and four libraries
are copied into the runtime; package-wide dependencies are not installed. Opus/Opusfile/Ogg
use BSD licenses; the URL helper's system OpenSSL dependency is checked on the host. Decoder
network syscalls are denied despite that linked helper. Existing system libc/libstdc++/
OpenSSL libraries remain system trust dependencies, not statically pinned artifacts.
License/copyright notices are retained in the runtime. HTTPS and pinned checksums were used;
no independent package-signature verification or comprehensive dependency CVE audit is claimed.
All native decoding/inference stays inside the sandbox. No root privileges or shared service
configuration changes occur. A prepared runtime is never silently overwritten.

## Bounded real acceptance

The fixture is8 seconds of the public JFK inaugural recording, sourced from the pinned
upstream sample and locally encoded as mono16kHz OGG/Opus. JFK's US federal speech recording
is public domain. Only this exact fixture hash is accepted by the current production wrapper;
there is no arbitrary audio argument. Decoding and inference run in separate Bubblewrap
namespaces with read-only mounts of the seven selected assets/input/system libraries, empty
HOME, no secrets/DB/project files, no network or process forks. Exact pthread flags are
allowed for reviewed native code. Each child has1 CPU affinity,768MiB virtual address-space,
10CPU seconds, no core dumps or writable files. Decoder wall deadline4s/output480KB;
recognizer18s/output16KB, stderr16KB. Exceeding any limit kills only that sandbox process
group and fails closed, with no host fallback. Worker30s alarm and lease checks remain.
768MiB is a virtual limit, not measured resident usage; initial unsandboxed local probe used
about100MiB RSS. Raw PCM duration and three expected English words are checked.

A hashed report records three real gates (asset pins, Opus decoding, English transcription),
source/model/runtime digests, measured duration and timings. The worker stores it immutably,
records typed evidence memory and notifies the owner. Plan10 shows a completed pilot subtask
while remaining in progress. Fake transport/unit evidence is not reported as actual speech.
Missing runtime/assets, wrong pins, malformed output and unavailable namespaces fail closed.

Local full suite565 passes, zero skips when all sandboxes/voice runtime are supplied; hosted
baseline skips17 host-dependent checks.14 new unit/integration tests cover pinned fixture,
policy/permissions, changed downloads/reports, scope/leases, immutable evidence, actual worker/
menu/partial Plan, native OGG transcription and a compiled canary proving file/network/fork/
write/credential denial. VPS deployment and actual queue receipts are recorded separately.
