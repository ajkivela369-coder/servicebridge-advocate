export type CinemaProviderKind = 'video'|'image'|'voice'|'dialogue-video'|'upscale'|'interpolate'|'mux';
export type CinemaProvider = {
  id:string;
  name:string;
  kind:CinemaProviderKind;
  role:string;
  quality:string;
  repo:string;
  license:string;
  commercialDefault:boolean;
  localRequirement:string;
  capabilities:string[];
  notes:string;
};

export const cinemaProviders:CinemaProvider[]=[
  {
    id:'wan22',
    name:'Wan2.2',
    kind:'video',
    role:'Commercial-friendly cinematic video default',
    quality:'Cinematic 720p / 24fps generation; T2V, I2V, TI2V and speech-to-video variants',
    repo:'https://github.com/Wan-Video/Wan2.2',
    license:'Apache-2.0',
    commercialDefault:true,
    localRequirement:'NVIDIA GPU; TI2V-5B can target 4090-class hardware',
    capabilities:['text-to-video','image-to-video','speech-to-video','character animation','cinematic prompts'],
    notes:'Primary open video engine when license simplicity matters.'
  },
  {
    id:'ltx2',
    name:'LTX-2 / LTX-2.5',
    kind:'video',
    role:'Cinematic Max audio+video engine',
    quality:'Native high-resolution audio-video generation, 4K pipeline support, multi-keyframe and camera controls',
    repo:'https://github.com/Lightricks/LTX-2',
    license:'LTX Community License',
    commercialDefault:false,
    localRequirement:'High-end NVIDIA GPU; exact memory depends on pipeline/quantization',
    capabilities:['text-to-video','image-to-video','synchronized audio','dialogue','multi-keyframe','camera control','4K pipeline'],
    notes:'Optional Max engine. License has extra conditions; keep separate from permissive defaults.'
  },
  {
    id:'flux-schnell',
    name:'FLUX.1-schnell',
    kind:'image',
    role:'Hero frames, character sheets and visual-style previews',
    quality:'High-quality text-to-image in 1–4 steps',
    repo:'https://github.com/black-forest-labs/flux',
    license:'Apache-2.0 for FLUX.1-schnell weights/code path',
    commercialDefault:true,
    localRequirement:'GPU strongly recommended',
    capabilities:['text-to-image','hero frames','character concepts','style preview cards','keyframe art'],
    notes:'Use schnell only for permissive commercial defaults; dev/Krea variants have different licenses.'
  },
  {
    id:'chatterbox',
    name:'Chatterbox',
    kind:'voice',
    role:'Natural narration and unique character voices',
    quality:'Expressive open TTS with voice prompting, emotion controls and paralinguistic tags',
    repo:'https://github.com/resemble-ai/chatterbox',
    license:'MIT',
    commercialDefault:true,
    localRequirement:'Python/PyTorch; CUDA recommended, Nano can run CPU',
    capabilities:['text-to-speech','voice prompting','multi-character voice palette','emotion','laugh/chuckle tags'],
    notes:'Only clone or condition on voices the user owns or has permission to use.'
  },
  {
    id:'musetalk',
    name:'MuseTalk 1.5',
    kind:'dialogue-video',
    role:'Lip-sync and dialogue close-ups',
    quality:'High-fidelity audio-driven lip synchronization',
    repo:'https://github.com/TMElyralab/MuseTalk',
    license:'MIT code; review bundled model/dependency terms when packaging weights',
    commercialDefault:true,
    localRequirement:'CUDA GPU recommended',
    capabilities:['lip-sync','dialogue shots','dubbing','character close-ups'],
    notes:'Use for original/authorized character footage and generated characters.'
  },
  {
    id:'realesrgan',
    name:'Real-ESRGAN',
    kind:'upscale',
    role:'4K finishing and restoration',
    quality:'Practical image/video super-resolution and artifact cleanup',
    repo:'https://github.com/xinntao/Real-ESRGAN',
    license:'BSD-3-Clause',
    commercialDefault:true,
    localRequirement:'GPU recommended; NCNN binaries available',
    capabilities:['2x/4x upscale','restoration','face enhancement integration','video frame enhancement'],
    notes:'Finishing pass after generation, not a substitute for strong source frames.'
  },
  {
    id:'rife',
    name:'RIFE',
    kind:'interpolate',
    role:'Motion smoothing and frame-rate finishing',
    quality:'Real-time/intermediate frame estimation; useful on diffusion-generated video',
    repo:'https://github.com/hzwer/ECCV2022-RIFE',
    license:'MIT',
    commercialDefault:true,
    localRequirement:'CUDA GPU recommended',
    capabilities:['frame interpolation','24→48/60fps','slow motion','diffusion-video smoothing'],
    notes:'Use carefully; interpolation can amplify visual artifacts.'
  },
  {
    id:'mediabunny',
    name:'Mediabunny',
    kind:'mux',
    role:'Browser MP4/audio assembly',
    quality:'Browser-native media encoding/muxing through WebCodecs',
    repo:'https://github.com/Vanilagy/mediabunny',
    license:'MPL-2.0',
    commercialDefault:true,
    localRequirement:'Modern browser with supported WebCodecs encoders',
    capabilities:['MP4 mux','canvas-to-video','audio track mux','metadata','local export'],
    notes:'Keeps the basic full-episode render path available even without a remote GPU renderer.'
  }
];

export const commercialCinemaDefaults={
  video:'wan22',
  image:'flux-schnell',
  voice:'chatterbox',
  dialogueVideo:'musetalk',
  upscale:'realesrgan',
  interpolate:'rife',
  mux:'mediabunny'
};

export const cinematicMaxDefaults={
  ...commercialCinemaDefaults,
  video:'ltx2'
};
