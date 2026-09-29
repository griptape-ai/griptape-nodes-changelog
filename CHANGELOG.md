# Griptape Nodes Changelog

Releases of every Griptape Nodes component, grouped by date, newest first. This file is
generated from each component's changelog, so edit those instead:

- [Engine](https://github.com/griptape-ai/griptape-nodes-engine/blob/HEAD/CHANGELOG.md)
- [Editor](https://github.com/griptape-ai/REDACTED/blob/HEAD/CHANGELOG.md)
- [Desktop](https://github.com/griptape-ai/REDACTED/blob/HEAD/CHANGELOG.md)

## 2026-09-29

### [Engine 0.103.0](https://github.com/griptape-ai/griptape-nodes-engine/compare/v0.102.0...v0.103.0)

#### Changed

- **Breaking:** The setting `worker.heartbeat_startup_grace_s` is now `worker.library_load_timeout_s`
  (env `GTN_CONFIG_WORKER__LIBRARY_LOAD_TIMEOUT_S`). With its heartbeat role removed, what it bounds
  is how long a worker may take to load its library, which the new name states. A config file still
  setting the old name silently falls back to the 600 second default.

#### Fixed

- The process a library runs isolated in shuts down within about 35 seconds of losing the engine
  that started it. Before, if that engine exited in the process's first 10 minutes, the process
  stayed up until those 10 minutes had passed. `worker.library_load_timeout_s` no longer delays
  that check; it still bounds how long the engine waits for the process to load its library.
  Setting `worker.heartbeat_timeout_s` below 30 seconds does not shorten this, on purpose: a busy
  engine can be slow to challenge, and a library's process must not read that as an engine that died.
- A library whose isolated process shuts down before loading it now reports that as soon as the
  process goes, instead of waiting out `worker.library_load_timeout_s` and then blaming a library
  load that never finished.
- Installing a library's dependencies no longer gives the engine an older copy of a package the
  engine itself imports. A library's environment comes ahead of the engine's own on the import path,
  so a library that resolved, for instance, an older `griptape` handed that copy to the engine too.
  Library installs now carry the engine's own versions as minimum versions, so such a package
  resolves no older than the engine's. A library that genuinely needs an older one is still
  installed and still works; it is now listed in that library's problems, naming what it supplies
  and what the engine expected, where before nothing connected the two.
  [#5681](https://github.com/griptape-ai/griptape-nodes-engine/issues/5681)
  [#5682](https://github.com/griptape-ai/griptape-nodes-engine/issues/5682)
- Creating or switching to a project whose workspace differs now closes the open workflow, returning
  you to the workflow picker. Before, the engine kept a workflow it no longer had a record of, so the
  next workflow you opened sat on "Checking workflow" and the log filled with "is not registered on
  this engine" warnings until you restarted the engine.
  [#5692](https://github.com/griptape-ai/griptape-nodes-engine/issues/5692)
- Saving a file from a workflow you have not saved yet no longer logs a stream of "Optional builtin
  'workflow_dir' could not be resolved" warnings. `workflow_dir` now answers with the folder your
  first save would default to, read from the project's `save_workflow` situation, so a project that
  points workflow saves outside the workspace root writes those files there rather than at the root.
  [#5669](https://github.com/griptape-ai/griptape-nodes-engine/issues/5669)
- Creating a versioned output folder or file sequence in a project no longer fails with "requires
  at most one unresolved variable" when its path uses a project directory such as `{outputs}`.
  `GetNextVersionIndexRequest` now fills in project directories and built-in variables itself, so
  callers only supply their own variables.
- A parameter that a node both shows and passes on, such as the text on a text node, keeps an edit
  made after the node has run. Before, reopening the workflow or refreshing the page showed the
  value from the last run instead of the edit.
- Renaming a parameter that holds an output value now reports that the old name no longer has one,
  alongside the new name's value. Before, only the new name was reported, so anything tracking
  output values by parameter name kept the old name's value.

#### Added

- `claude-sonnet-5-5` is available in Griptape Cloud model dropdowns and the chat sidebar.
- Projects have two new situations for versioned output folders. `save_output_directory` creates
  `{outputs}/renders_v001`, then `renders_v002` on the next run. `save_file_sequence` writes each
  run's frames into a new version folder, such as `frames_v001/frames.0001.png`. Node libraries
  use them through `ProjectDirectoryParameter` and `ProjectFileSequenceParameter`. Projects on
  the legacy template fall back to the same layout. See
  [Situations](https://docs.griptapenodes.com/en/stable/guides/projects/situations/#save_output_directory).

### [Editor 127](https://github.com/griptape-ai/REDACTED/compare/v126...v127)

#### Added

- The "Controls under minimap" beta feature moves the canvas controls to a compact horizontal bar
  directly below the minimap, in the bottom-right corner. The bar includes zoom out, a percentage
  dropdown with preset zoom levels (25 %–200 %), zoom in, fit view, a minimap toggle, and a grid
  settings button. The grid button opens a popover to show or hide the background grid, change the
  grid type (Cross, Dots, Lines), adjust grid size and gap with sliders, and enable snapping with
  a configurable snap size. It is on by default; the bar appears when Settings → General → "Show
  Canvas Controls" is enabled.
  [#3040](https://github.com/griptape-ai/REDACTED/issues/3040)
- Settings has a "Beta Features" page for turning unfinished features on before they become the
  default. Open it from Settings → Settings → "Beta Features" or the `#settings-beta` URL hash.
  Engines that list their own beta features show them there too. The first one, "Toolbar placement
  button", moves the floating canvas toolbar between the top and bottom of the canvas.
  [#3013](https://github.com/griptape-ai/REDACTED/issues/3013)
- The "Workflow Already Exists" dialog can save the workflow under a free name, such as
  `Sales Report 2`, in the same folder, instead of only overwriting or cancelling.
  [#2850](https://github.com/griptape-ai/REDACTED/issues/2850)
- The `#billing` URL hash opens the billing dialog, so a host with its own account menu can open
  it.
- When libraries have updates, the Libraries panel on the left sidebar shows an "N updates
  available" button in its header that opens the Library Manager on its "Updates" filter.
- The Library Manager shows a bar above the list when libraries have updates, with an "Update All"
  button that updates them in turn. Updates held back by the minimum release age are skipped.
- Beta feature "Individual node toolbars in multi-select", on by default: each selected node shows
  its own toolbar, and its buttons act on that node only. The single shared toolbar that appeared
  when several nodes were selected is gone. Lock, duplicate, and delete for the whole selection are
  in the main canvas toolbar and also work with one node selected. Zoomed out below 40%, node
  toolbars fade out until you hover the node. Change that level with "Toolbar fade zoom threshold"
  in Settings → Editor → "Button Customization". Turn the feature off in Settings → "Beta Features".
  [#3017](https://github.com/griptape-ai/REDACTED/issues/3017)

#### Changed

- **Breaking:** The editor asks its host to send Griptape Cloud requests, so credits, usage, and
  billing load on on-prem installs that reach Griptape Cloud through an admin server. Hosts that
  embed the editor need `@griptape-ai/nodes-bridge` 0.6.0, which cannot serve earlier editor
  builds, so update the bridge and the editor together.
  [REDACTED#434](https://github.com/griptape-ai/REDACTED/issues/434)
- The left sidebar is now a narrow icon rail that no longer expands. Your account, credits,
  billing, and "Admin Dashboard" move into an account menu at the top right of the editor, and
  light and dark mode move to Settings → "Theme Settings". To get the expandable sidebar back, turn
  off "Compact sidebar" in Settings → "Beta Features".
- The Library Manager's buttons now have labels and sit together in its header: "Check for
  updates", "Refresh Libraries", and "Add Library". "Refresh Libraries" reloads libraries in the
  engine, like the button in the sidebar, instead of only re-reading the list. The "All",
  "Updates", and "Errors" filters sit in their own row as a switch so they no longer look like
  buttons.
- The app header has no gradient and gains a bottom border that separates it from the canvas in
  dark mode. The File, Manage, Settings, and Help menus no longer sit in a bordered box.
  [#3024](https://github.com/griptape-ai/REDACTED/issues/3024)

#### Removed

- The "Show Zoom Control" setting and its zoom slider (top-left of the canvas) have been removed.
  Zoom controls are now part of the "Controls under minimap" feature, available via Settings →
  General → "Show Canvas Controls".
- The faded Griptape Nodes logo no longer shows in the top-right corner of the canvas.
  [#3002](https://github.com/griptape-ai/REDACTED/issues/3002)

#### Fixed

- In the dark theme, red icons, error text, and delete buttons are now readable. In both themes,
  delete buttons, remove icons, and menu items across the editor and the Admin Dashboard now share
  one style, so they all turn or stay red on hover instead of some turning white or gray.
- The library update checks set in Settings → "Libraries" now run when the left sidebar is
  collapsed or closed. They used to run only while the sidebar was expanded.
- Unlimited accounts no longer show "Unlimited credit" in orange or red as if the balance were
  running low.
- Manage Projects → "Register Template..." now saves the open workflow, returns you to the workflow
  picker, and refreshes the sidebar for the project it activates, matching every other way of
  switching projects. Before, registering a project whose workspace differs lost unsaved edits and
  left the editor showing a workflow the engine had closed.
- Resizing the right sidebar no longer freezes when the mouse pauses mid-drag. Pressing just left
  of its edge no longer leaves a selection box following the cursor over the canvas.
  [#3044](https://github.com/griptape-ai/REDACTED/issues/3044)
- Duplicating a group or pasting copied nodes keeps their layout instead of stacking them in one
  spot, and Cmd+D creates each group child once. Nodes created inside a group from the Tab menu
  join the group, and a node the engine refuses to add to a group leaves it and shows an error.
  [#2962](https://github.com/griptape-ai/REDACTED/issues/2962)

## 2026-09-24

### [Engine 0.102.0](https://github.com/griptape-ai/griptape-nodes-engine/compare/v0.101.0...v0.102.0)

#### Added

- Libraries can list heavy packages under `pip_dependencies_exec` in their manifest. Those install
  into a separate `.venv-exec` and load only in the library's own process, where its nodes run, so
  libraries with clashing heavy pins can be installed side by side.
- A node in a library that runs isolated in a worker can hand an unserializable value, such as a
  diffusers pipeline or a latent tensor, to the next node. Mark the producing output
  `serializable=False` and the engine holds the object in the worker, sending an opaque key in its
  place that the consuming node's read resolves. See
  [MIGRATION.md](https://github.com/griptape-ai/griptape-nodes-engine/blob/HEAD/MIGRATION.md#serializablefalse-outputs-are-held-in-their-own-process-across-a-worker-boundary).
- Claude Opus 5.5, GPT-6 Sol, and GPT-6 Luna are in the model catalog.
- Nodes can implement `validate_in_execution_environment()` to run a check where the node itself runs,
  which for a library isolated in its own process is where its heavy packages are importable and its
  inputs are the real objects. A node that fails the check reports why in
  `ExecuteNodeResultFailure.validation_exceptions` instead of crashing partway through.
- You can try new features early by turning them on from the **Beta Features** page in the
  editor's settings, and turn them off again at any time. Node libraries can offer beta features
  of their own. See
  [Beta Features](https://docs.griptapenodes.com/en/stable/guides/editor/beta_features/), and
  [Authoring Libraries](https://docs.griptapenodes.com/en/stable/development/custom_nodes/authoring_libraries/#beta-features)
  to add them to a library.
- The `Slider` trait, and `ParameterInt` and `ParameterFloat` with `slider=True`, take
  `soft_limits=True`. The slider then spans its range, but a value typed outside it is accepted
  instead of rejected, matching soft limits in Nuke, Maya, and Houdini.
  [#5269](https://github.com/griptape-ai/griptape-nodes-engine/issues/5269)
- Custom traits can keep settings a node changes at runtime, such as a narrowed range, when the
  workflow is saved and reopened, by implementing `to_state()` and `apply_state()`. See
  [MIGRATION.md](https://github.com/griptape-ai/griptape-nodes-engine/blob/HEAD/MIGRATION.md#traits-can-save-runtime-state).

#### Changed

- **Breaking:** `WorkflowPackager.package_to_folder` returns a `PackagedBundle` with the bundled
  workflow's path and the library paths, instead of a list of library paths. See
  [MIGRATION.md](https://github.com/griptape-ai/griptape-nodes-engine/blob/HEAD/MIGRATION.md#package_to_folder-reports-where-it-put-the-workflow).
  [#5326](https://github.com/griptape-ai/griptape-nodes-engine/issues/5326)
- An app event raised in one process is no longer delivered to listeners in another. A library running
  isolated in its own process reports to the engine by sending a request instead.
- **Breaking:** When a parameter's `ui_options` and a custom trait set the same key, the trait's
  value now wins, so node code can no longer override a trait's widget settings through
  `ui_options`. Implement `state_from_ui_options()` on the trait to accept these overrides, or
  change the trait's own attributes instead.
- Setting a value outside a `Slider` range now fails with an error naming the parameter, the value,
  and the allowed range, instead of "Value out of range".
  [#5269](https://github.com/griptape-ai/griptape-nodes-engine/issues/5269)

#### Removed

- **Breaking:** `LibraryLoadedNotification` no longer carries `node_schemas`. A library that loaded in
  its own process reports its schemas to the engine with the new `ReportLibraryLoadedRequest`, and the
  notification that follows says only how the load went.
- `TraitRegistry` and `Trait.get_trait_keys()` are removed, with no replacement, since nothing read
  them. Custom traits no longer need to implement `get_trait_keys()`, and existing implementations
  can be deleted.
- The engine no longer runs its own static file server. The Griptape Nodes app serves the
  workspace, as it has since v0.95.0. `STATIC_SERVER_ENABLED` is gone.

#### Fixed

- Connecting a video, image, or audio file uploaded through the editor to a node that requires that
  media type no longer fails with a message saying the parameter must be an artifact.
- Image, video, audio, and 3D parameters no longer fail when given an inline `data:` URI longer than
  the operating system's file name limit, which any real image exceeds. The URI is kept as the
  parameter's value.
- Model dropdowns no longer mark every model "Not permitted by your license" when two installed
  libraries provide a node with the same name.
  [#5618](https://github.com/griptape-ai/griptape-nodes-engine/issues/5618)
- Group nodes in a reopened workflow show the ports and connections of parameters added to the
  group again.
  [#5563](https://github.com/griptape-ai/griptape-nodes-engine/issues/5563)
- A node can be deleted while a workflow is running. Deleting a node the run still needs cancels the
  run; deleting any other node lets it finish.
- Image previews no longer break when several requests regenerate the same preview at once, and
  synced or copied images are no longer treated as changed on every view. When a preview cannot be
  made, the engine reports why.
- Workflows created from a template or by branching are saved where the project saves workflows,
  instead of always in the workspace folder. Branching twice no longer overwrites the first branch.
- Packaging a workflow stops with an error when the workflow or one of its files has the same name
  as a file the bundle reserves.
  [#5323](https://github.com/griptape-ai/griptape-nodes-engine/issues/5323)
- `RunWorkflowWithCurrentStateRequest` fails when a workflow is already open, instead of attaching
  the target as a hidden flow that was saved and run along with the open workflow.
  [#5526](https://github.com/griptape-ai/griptape-nodes-engine/issues/5526)
- A slider range, dropdown choices, or button link that a node changes at runtime now survives
  saving and reopening the workflow. Before, the reopened workflow showed the saved settings, but
  sliders checked the old range, dropdowns the old choices, and buttons opened the old link.
  [#5440](https://github.com/griptape-ai/griptape-nodes-engine/issues/5440)
- Changing a slider's range or a dropdown's choices through `ui_options`, from node code or the
  editor, now also changes which values the parameter accepts. Before, the editor showed the new
  range or choices, but the parameter still checked values against the old ones.
  [#5440](https://github.com/griptape-ai/griptape-nodes-engine/issues/5440)
- Nodes in a library that runs isolated in its own process no longer stop working mid-session while
  the engine is busy. That process is now dropped for leaving heartbeat challenges unanswered rather
  than for elapsed time, so `worker.heartbeat_timeout_s` bounds unanswered challenges instead of
  wall-clock silence.
- A node that writes a list or dictionary to an output and reads it back gets the same object rather
  than a copy of it, and a value that refers to itself no longer fails the node with a
  `RecursionError`. Inline `{VAR}` substitution returns a value it did not rewrite unchanged.

## 2026-09-15

### [Desktop 0.26.0](https://github.com/griptape-ai/REDACTED/compare/v0.25.1...v0.26.0)

#### Changed

- The bundled version of the Griptape Nodes app has been updated to `0.98.0`.
- The bundled version of the editor has been updated to `0.125.0`.

## 2026-09-11

### [Desktop 0.25.1](https://github.com/griptape-ai/REDACTED/compare/v0.25.0...v0.25.1)

#### Fixed

- The engine no longer quits at startup over its local socket transport, which
  the app never used. Creating that socket failed on some macOS machines, which
  left the app unusable.
- The app no longer fails to launch with "A JavaScript error occurred in the main
  process" when your Documents folder cannot be located, which could happen when
  iCloud Drive's "Desktop & Documents Folders" sync left the folder unavailable.

## 2026-09-07

### [Desktop 0.25.0](https://github.com/griptape-ai/REDACTED/compare/v0.24.0...v0.25.0)

#### Added

- Links from the web editor can now open here instead. A link to a library or a
  settings page hands off to the app, which opens it against the engine on your
  own machine.

#### Changed

- The bundled version of the Griptape Nodes app has been updated to `0.97.0`.

#### Fixed

- Chat sidebar agents no longer fail to respond after an incompatible dependency
  update broke them.
- The editor no longer disconnects after the app window has been covered by
  another application or minimized for a few minutes.

## 2026-09-01

### [Desktop 0.24.0](https://github.com/griptape-ai/REDACTED/compare/v0.23.2...v0.24.0)

#### Added

- The update notification and the Updates section in Settings now have a "What's New" button that shows the release notes for the new version before you install it.
- Release notes for each version are now published to the update feed, so they can be read before installing an update.
- Administrators can now turn off app updates on a deployed machine with a `policy.json` file, so an install can arrive with updates already off without anyone visiting Settings.

#### Changed

- The bundled version of the Griptape Nodes app has been updated to `0.96.0`.
- The bundled version of the editor has been updated to `0.124.0`.

#### Fixed

- Setting update behavior to Silence now stops the automatic update check itself, rather than only hiding the notification. Checking manually from Settings or the app menu still works.
- On macOS, the window buttons are now vertically centered in the app header. The sign-in and first-run screens use that same header, so it is clear where the window can be dragged.
- Opening the Engine Monitor in its own window now focuses the window that is already open instead of stacking up duplicate copies.

## 2026-08-19

### [Desktop 0.23.2](https://github.com/griptape-ai/REDACTED/compare/v0.23.1...v0.23.2)

#### Changed

- The bundled version of the Griptape Nodes app has been updated to `0.95.1`.
- The bundled version of the editor has been updated to `0.123.1`.

## 2026-08-18

### [Desktop 0.23.1](https://github.com/griptape-ai/REDACTED/compare/v0.23.0...v0.23.1)

#### Fixed

- Opening the Admin Dashboard no longer flashes "Couldn't determine your organization" before your organization finishes loading.

### [Desktop 0.23.0](https://github.com/griptape-ai/REDACTED/compare/v0.22.3...v0.23.0)

#### Added

- The Griptape server endpoint can now be reset back to its default from Settings and from the license sign-in screen.
- The Admin Dashboard can now switch which organization you are administering, and shows each organization's tier.
- Organizations can now be renamed, and you can leave an organization you were invited to. Leaving the organization the app is working in moves the app to another one and restarts the engine.

#### Changed

- The bundled version of the Griptape Nodes engine has been updated to `0.98.0`.
- Organization management (members, invitations, creating an organization) has moved from its own page into the Admin Dashboard, so it is now the same in the desktop app and the browser editor. "Manage Organizations..." opens it there.
- The Admin Dashboard is now available whenever you are signed in to Griptape Cloud, including while working in an organization you were invited to.

#### Fixed

- A custom Griptape server endpoint is now used only by license sign-ins, so it no longer redirects sessions signed in through Griptape Cloud.
- The credit balance in the editor now follows the organization selected in the app, so it no longer shows another organization's credits until you switch away and back.
- The Admin Dashboard now shows your email instead of "User".
- The Permission Editor's engine picker now lists only engines in the organization you are administering.

## 2026-08-07

### [Desktop 0.22.3](https://github.com/griptape-ai/REDACTED/compare/v0.22.2...v0.22.3)

#### Fixed

- The bundled Git now runs on all supported Linux distributions, including RHEL 8 derivatives such as Rocky Linux 8.

## 2026-08-05

### [Desktop 0.22.2](https://github.com/griptape-ai/REDACTED/compare/v0.22.1...v0.22.2)

#### Fixed

- Resolved issue with context menu not opening in certain scenarios.

### [Desktop 0.22.1](https://github.com/griptape-ai/REDACTED/compare/v0.22.0...v0.22.1)

#### Fixed

- Right-clicking an image or video in the editor now opens the standard menu, so media can be copied and pasted again.

## 2026-08-04

### [Desktop 0.22.0](https://github.com/griptape-ai/REDACTED/compare/v0.21.4...v0.22.0)

#### Changed

- The bundled version of the Griptape Nodes engine has been updated to `0.95.0`.
- The ability to purchase credits has been disabled for license users.

#### Fixed

- Linux builds start again on distributions with glibc 2.28.
- The Admin Dashboard now acts on the organization selected in the app, so licenses are created in and billed to the organization you expect.

## 2026-08-03

### [Desktop 0.21.4](https://github.com/griptape-ai/REDACTED/compare/v0.21.3...v0.21.4)

#### Added

- The app now ships with its own copy of Git.

#### Fixed

- Resolved connection issue with the editor's agent sidebar.

### [Desktop 0.21.3](https://github.com/griptape-ai/REDACTED/compare/v0.21.2...v0.21.3)

#### Added

- A license key can now be supplied at launch through the `GRIPTAPE_NODES_LICENSE` environment variable, so machines can be provisioned without anyone pasting a key into Settings.
- Linux builds now run on distributions with glibc 2.28 or newer.
