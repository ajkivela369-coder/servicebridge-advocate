# GrimForge — Chronicles-quality production workflow

Quality target: long-form AI cinematic storytelling with the production discipline seen in projects such as *The Chronicles of Bone*. GrimForge should reproduce the **workflow principles**, not a creator's protected scripts, shots, characters, voices, or visual identity.

## Website-first architecture

The React website is the control room. Heavy generation runs behind provider adapters on a GPU service.

Simple Mode should hide the complexity. Pro Mode exposes it.

### Simple Mode

1. Paste a public reference video/channel/site.
2. Describe the original episode.
3. Choose runtime and a quality tier.
4. Veyr builds the production bible and generates the episode in reviewed shot batches.
5. User receives a full episode player and can jump to Pro for any scene.

### Pro Mode

Expose the production bibles, provider stack, seeds/references, shot batches, voice casting, sound layers, render settings, upscaling, interpolation, and final assembly.

## 1. Style Bible before motion

For every recurring character, generate and lock:
- hero portrait
- full-body neutral
- wide / medium / close-up
- front / 3-quarter / profile / rear
- wardrobe and material notes
- eye/hair/skin/scar/tattoo identifiers
- prop/weapon sheet
- forbidden drift notes
- voice ID and emotional range

Use the bible as image-to-image/keyframe conditioning for later shots.

## 2. Set Bible / 360° quadrant strategy

For each recurring location:
- North master
- East master
- South master
- West master
- overhead / tactical map when useful
- day / dusk / night lighting states
- key landmarks
- door/window/stair orientation
- environmental motion notes

Every shot references a set master so geography does not drift between cuts.

## 3. Universal cinematography grammar

Every motion prompt is assembled from:
- subject + ACTION (not just nouns)
- shot size
- focal length / lens feel
- camera height
- camera move
- blocking
- foreground / midground / background depth
- motivated lighting
- atmosphere / particles
- continuity anchor from prior shot
- physics instruction
- end-frame intention

GrimForge stores this as a reusable Cinematic Suffix and varies only the action/camera decisions that belong to the shot.

## 4. Generate takes, not miracles

For high-value shots:
- generate 4–12 takes
- preserve seed and character/set references
- score continuity, anatomy, performance, camera, lip-sync and usable duration
- keep the best 2–5 second fragments if a full take is imperfect
- allow the editor to mark a Golden Take

This is the default behavior for battle/action shots in Cinema and Max modes.

## 5. Build in near-final sequences

Do not generate a 15-minute film blindly and fix it later.

Generate and lock roughly 20–45 seconds at a time:
1. storyboard / shot plan
2. hero frames
3. motion clips
4. voice/dialogue
5. sound effects / ambience
6. rough edit
7. continuity check
8. approve sequence
9. continue

The next sequence receives the approved last frame, character bible, set bible and continuity state.

## 6. Voice casting

Use Chatterbox or another authorized expressive TTS provider.

Each original character gets:
- persistent voice ID
- pitch/timbre range
- speed/cadence
- emotional intensity
- diction
- allowed paralinguistic tags
- pronunciation dictionary

Narrator and dialogue voices are separate tracks.

Never clone a real person's voice without authorization.

## 7. Dialogue shots

For visible dialogue:
- generate/choose final character audio first
- use audio-driven video or lip-sync (Wan S2V, MuseTalk, or a configured provider)
- preserve character image/identity references
- cut away strategically rather than forcing every spoken line into a continuous talking-head shot

## 8. Sound is a production layer

Maintain separate tracks for:
- narration
- character dialogue
- natural production sound
- Foley / impacts
- ambience
- score
- room tone / environmental bed

Generate natural sound separately from music where possible, then mix in post.

## 9. Quality tiers

### Draft
Fast storyboard / animatic.
- still/keyframe generation
- local TTS
- browser MP4 assembly

### Cinema
Default publishable target.
- FLUX.1-schnell or configured still engine
- Wan2.2 motion generation
- Chatterbox voices
- MuseTalk/Wan S2V dialogue shots
- Real-ESRGAN finishing
- RIFE where motion benefits
- final assembly

### Cinematic Max
Highest-quality / higher-compute mode.
- LTX-2.x or configured premium/open model for selected shots
- multi-keyframe conditioning
- take generation + Golden Take selection
- highest-resolution finishing
- 4K delivery when the source quality justifies it

LTX licensing and compute requirements must be acknowledged before enabling this tier.

## 10. Style-choice UX

Never show abstract placeholder shapes as the primary style selector.

Each style card must show the **same representative shot** rendered in that mode:
- Cinematic 3D
- 2.5D parallax art
- painterly dark fantasy
- tactical holo-map
- manuscript / archive
- graphic motion-comic

Cards should include:
- actual thumbnail
- motion description
- best-use label
- expected compute/cost
- Compare Same Shot button

## 11. Continuity memory

Every approved scene updates:
- character state (injury, dirt, props, costume)
- location / camera axis
- time of day
- weather
- army/crowd positions
- emotional state
- active objects
- last approved frame

Veyr must feed this continuity packet into subsequent scene prompts.

## 12. Full episode output

A Simple Mode run is not "done" when the screenplay exists.

Done means the app contains:
- episode script
- voices/audio
- approved/generative visual clips or explicit failed-shot markers
- sound layers
- timeline
- final assembled playable output
- exportable MP4 when a render/mux path is available
- scene-level provenance and provider metadata
