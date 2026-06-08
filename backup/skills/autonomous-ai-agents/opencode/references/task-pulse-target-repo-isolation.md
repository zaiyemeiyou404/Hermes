# Task Pulse + OpenCode target-repo isolation

Use this when a Task Pulse task is supposed to improve some external GitHub repository rather than Task Pulse itself.

## Failure mode seen in practice

- Task created with `cwd=/home/ubuntu/task-pulse`
- Prompt referenced `https://github.com/<owner>/<repo>` but did not force a separate clone/workdir
- OpenCode inspected the URL, then edited files in the local Task Pulse checkout because that was the writable repo already in front of it
- A follow-up attempt told it to clone into `/tmp/...`, but the runner rejected the external directory request

## Durable fix pattern

Prompt requirements:

1. clone target repo into an allowed subdirectory under the current workspace, e.g. `/home/ubuntu/task-pulse/projects/<repo>-<task>`
2. if that directory exists, remove/recreate it or make the prompt specify the desired behavior
3. create and switch to a named branch before changing files
4. explicitly state: do not modify the orchestration repo / do not modify Task Pulse itself
5. require final output to include:
   - working directory
   - branch name
   - modified files
   - verification commands run

## Verification from Hermes side

After launch, check:

```bash
git -C /home/ubuntu/task-pulse/projects/<repo-dir> status --short --branch
```

Good signs:
- branch name matches the requested task branch
- modified files are in the target repo, not Task Pulse
- Task Pulse logs show file edits after clone/branch setup, not just prompt planning

## Example prompt fragment

```text
Please work in /home/ubuntu/task-pulse/projects/agent-taskpulse-v3.
Clone https://github.com/zaiyemeiyou404/agent there, create branch task-pulse/agent-polish-v3, and do not modify the Task Pulse repo itself.
Your final output must include the working directory, branch name, modified files, and validation results.
```
