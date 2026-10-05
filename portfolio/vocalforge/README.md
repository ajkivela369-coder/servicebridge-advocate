# VocalForge

Current local implementation is maintained in the private Forge AI Suite repository under apps/vocalforge. This portfolio folder records its build history; no hosted production URL is claimed.

## October 5 quality review

The laptop audit found exports reaching the digital peak limit and noise receiving a pitch estimate. The reviewed fix enforces sample-peak headroom, filters unreliable pitch estimates and labels opening level separately from an isolated noise floor. Four vocal regressions passed in the dedicated vocal environment.

Perceptual voice quality, microphone/device behavior and VST3 loading still require listening/device acceptance. DeepFilterNet and validated third-party VST3 processing remain future work.

See BUILD_AND_UPGRADE.md for the implementation history.
