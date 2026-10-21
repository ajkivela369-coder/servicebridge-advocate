import type { RetrievalDoc } from "./semantic";

export type Topic =
  | "action_potential"
  | "synaptic_plasticity"
  | "microglia"
  | "myelin"
  | "astrocytes"
  | "blood_brain_barrier"
  | "dopamine"
  | "gaba"
  | "serotonin"
  | "cerebellum";

export type QueryType = "direct" | "paraphrase" | "mechanism" | "indirect" | "multi";
export type Difficulty = "easy" | "medium" | "hard";

export type DatasetDocument = RetrievalDoc & {
  topic: Topic | "distractor";
  title: string;
  sourceType: "synthetic";
};

export type RetrievalBenchmarkCase = {
  id: string;
  familyId: string;
  topic: Topic;
  query: string;
  relevantIds: string[];
  note: string;
  queryType: QueryType;
  difficulty: Difficulty;
};

export const RETRIEVAL_DOCS: DatasetDocument[] = [
  {
    id: "D001",
    topic: "action_potential",
    title: "Action-potential depolarization and repolarization",
    sourceType: "synthetic",
    text: "Voltage-gated sodium channels open rapidly during the rising phase of a neuronal action potential, producing sodium influx and membrane depolarization. Delayed opening of voltage-gated potassium channels contributes to repolarization as potassium leaves the cell.",
  },
  {
    id: "D002",
    topic: "action_potential",
    title: "Refractory periods",
    sourceType: "synthetic",
    text: "The absolute refractory period largely reflects inactivation of voltage-gated sodium channels. During the relative refractory period, persistent potassium conductance and incomplete recovery of sodium channels make another action potential harder to trigger.",
  },
  {
    id: "D003",
    topic: "synaptic_plasticity",
    title: "NMDA receptors and calcium entry",
    sourceType: "synthetic",
    text: "At many excitatory synapses, NMDA receptors require glutamate binding and sufficient postsynaptic depolarization to relieve magnesium block. Calcium entry through active NMDA receptors can initiate signaling pathways involved in long-term potentiation.",
  },
  {
    id: "D004",
    topic: "synaptic_plasticity",
    title: "AMPA receptor trafficking in LTP",
    sourceType: "synthetic",
    text: "Long-term potentiation can increase synaptic strength through signaling that promotes insertion or stabilization of AMPA receptors at the postsynaptic membrane, increasing responsiveness to subsequent glutamate release.",
  },
  {
    id: "D005",
    topic: "microglia",
    title: "Microglial immune surveillance",
    sourceType: "synthetic",
    text: "Microglia are resident immune cells of the central nervous system. They survey the local environment, respond to injury or infection, and can produce inflammatory or regulatory signals depending on context.",
  },
  {
    id: "D006",
    topic: "microglia",
    title: "Microglia and synaptic remodeling",
    sourceType: "synthetic",
    text: "During development and in some activity-dependent settings, microglia can participate in synaptic remodeling and pruning by interacting with synaptic elements and complement-related signaling pathways.",
  },
  {
    id: "D007",
    topic: "myelin",
    title: "Oligodendrocytes and CNS myelin",
    sourceType: "synthetic",
    text: "Oligodendrocytes form myelin around axons in the central nervous system. Myelin enables saltatory conduction between nodes of Ranvier and increases the speed and efficiency of action-potential propagation.",
  },
  {
    id: "D008",
    topic: "myelin",
    title: "Schwann cells and PNS myelin",
    sourceType: "synthetic",
    text: "Schwann cells myelinate axons in the peripheral nervous system. A myelinating Schwann cell wraps a segment of one axon, supporting rapid saltatory conduction along peripheral nerves.",
  },
  {
    id: "D009",
    topic: "astrocytes",
    title: "Astrocyte ion and neurotransmitter regulation",
    sourceType: "synthetic",
    text: "Astrocytes help regulate extracellular potassium and clear neurotransmitters such as glutamate from the synaptic environment. These functions contribute to neuronal homeostasis and controlled excitability.",
  },
  {
    id: "D010",
    topic: "astrocytes",
    title: "Astrocyte metabolic and vascular support",
    sourceType: "synthetic",
    text: "Astrocytes provide metabolic support to neurons and communicate with nearby blood vessels. Their endfeet contact the neurovascular interface and contribute to regulation of the extracellular environment.",
  },
  {
    id: "D011",
    topic: "blood_brain_barrier",
    title: "Endothelial tight junctions at the BBB",
    sourceType: "synthetic",
    text: "The blood-brain barrier is formed primarily by specialized brain endothelial cells connected by tight junctions. These junctions restrict paracellular movement and help control which substances enter neural tissue from the circulation.",
  },
  {
    id: "D012",
    topic: "blood_brain_barrier",
    title: "BBB transport and supporting cells",
    sourceType: "synthetic",
    text: "Blood-brain barrier function also depends on selective transport systems and interactions among endothelial cells, pericytes, basement membrane, and astrocytic endfeet within the neurovascular unit.",
  },
  {
    id: "D013",
    topic: "dopamine",
    title: "Dopamine and reward prediction error",
    sourceType: "synthetic",
    text: "Midbrain dopamine neurons can change firing in relation to reward prediction errors, helping update expectations when outcomes are better or worse than predicted. Dopamine contributes to reinforcement learning rather than serving as a simple pleasure signal.",
  },
  {
    id: "D014",
    topic: "dopamine",
    title: "Nigrostriatal dopamine and movement",
    sourceType: "synthetic",
    text: "Dopamine from substantia nigra pars compacta neurons modulates basal-ganglia circuits involved in movement. Loss of these dopaminergic neurons is a major feature of Parkinson disease.",
  },
  {
    id: "D015",
    topic: "gaba",
    title: "GABA-A fast inhibition",
    sourceType: "synthetic",
    text: "GABA-A receptors are ionotropic chloride channels that usually mediate fast inhibitory synaptic transmission in the mature central nervous system. Their effect depends on the chloride electrochemical gradient.",
  },
  {
    id: "D016",
    topic: "gaba",
    title: "GABA-B slow inhibition",
    sourceType: "synthetic",
    text: "GABA-B receptors are metabotropic G-protein-coupled receptors. They can produce slower inhibitory effects by modulating potassium and calcium channels and intracellular signaling pathways.",
  },
  {
    id: "D017",
    topic: "serotonin",
    title: "Raphe serotonin projections",
    sourceType: "synthetic",
    text: "Many serotonin-producing neurons are located in raphe nuclei of the brainstem and project broadly through the brain. Serotonergic signaling can influence mood, arousal, sleep, appetite, and other functions.",
  },
  {
    id: "D018",
    topic: "serotonin",
    title: "Serotonin receptor diversity",
    sourceType: "synthetic",
    text: "Serotonin acts through multiple receptor families with different signaling mechanisms. Most serotonin receptors are G-protein-coupled, while the 5-HT3 receptor is a ligand-gated ion channel.",
  },
  {
    id: "D019",
    topic: "cerebellum",
    title: "Cerebellar coordination and error correction",
    sourceType: "synthetic",
    text: "The cerebellum contributes to coordination, timing, motor learning, and error correction by comparing ongoing movement-related signals with expected outcomes and adjusting motor commands.",
  },
  {
    id: "D020",
    topic: "cerebellum",
    title: "Purkinje-cell output",
    sourceType: "synthetic",
    text: "Purkinje cells are the principal output neurons of the cerebellar cortex. They are inhibitory and use GABA to influence neurons in the deep cerebellar nuclei.",
  },
  {
    id: "D021",
    topic: "distractor",
    title: "Hypothalamic homeostasis",
    sourceType: "synthetic",
    text: "The hypothalamus coordinates endocrine, autonomic, and behavioral responses that contribute to homeostasis, including temperature regulation, energy balance, thirst, and circadian control.",
  },
  {
    id: "D022",
    topic: "distractor",
    title: "Hippocampal memory",
    sourceType: "synthetic",
    text: "The hippocampal formation is important for forming and organizing declarative memories and for aspects of spatial representation.",
  },
  {
    id: "D023",
    topic: "distractor",
    title: "Neuromuscular acetylcholine",
    sourceType: "synthetic",
    text: "At the skeletal neuromuscular junction, motor neurons release acetylcholine, which binds nicotinic receptors on muscle fibers and initiates an end-plate potential.",
  },
  {
    id: "D024",
    topic: "distractor",
    title: "HPA stress axis",
    sourceType: "synthetic",
    text: "The hypothalamic-pituitary-adrenal axis coordinates an endocrine stress response through corticotropin-releasing hormone, adrenocorticotropic hormone, and glucocorticoid release.",
  },
  {
    id: "D025",
    topic: "distractor",
    title: "Retinal phototransduction",
    sourceType: "synthetic",
    text: "In retinal photoreceptors, light activates opsins and a G-protein signaling cascade that lowers cyclic GMP, closes cation channels, and hyperpolarizes the photoreceptor.",
  },
];

export const RETRIEVAL_BENCHMARK: RetrievalBenchmarkCase[] = [
  { id: "Q001", familyId: "AP_01", topic: "action_potential", query: "Which channels drive the rising and falling phases of a neuronal action potential?", relevantIds: ["D001"], note: "Direct channel vocabulary.", queryType: "direct", difficulty: "easy" },
  { id: "Q002", familyId: "AP_02", topic: "action_potential", query: "What membrane proteins make a neuron rapidly become positive and then return toward resting voltage?", relevantIds: ["D001"], note: "Semantic paraphrase of depolarization and repolarization.", queryType: "paraphrase", difficulty: "medium" },
  { id: "Q003", familyId: "AP_03", topic: "action_potential", query: "Why does sodium enter before potassium exits during a typical spike?", relevantIds: ["D001"], note: "Mechanistic timing query.", queryType: "mechanism", difficulty: "medium" },
  { id: "Q004", familyId: "AP_04", topic: "action_potential", query: "Why can a neuron not immediately fire another full action potential after the first one?", relevantIds: ["D002"], note: "Refractory-period query with indirect wording.", queryType: "indirect", difficulty: "medium" },
  { id: "Q005", familyId: "AP_05", topic: "action_potential", query: "Which processes both generate the spike and temporarily limit immediate re-firing?", relevantIds: ["D001", "D002"], note: "Multi-passage question spanning channel dynamics and refractoriness.", queryType: "multi", difficulty: "hard" },

  { id: "Q006", familyId: "LTP_01", topic: "synaptic_plasticity", query: "How do NMDA receptors contribute to long-term potentiation?", relevantIds: ["D003"], note: "Direct receptor/plasticity query.", queryType: "direct", difficulty: "easy" },
  { id: "Q007", familyId: "LTP_02", topic: "synaptic_plasticity", query: "What coincidence detector at excitatory synapses can allow calcium into a postsynaptic neuron?", relevantIds: ["D003"], note: "Paraphrase of glutamate plus depolarization requirement.", queryType: "paraphrase", difficulty: "medium" },
  { id: "Q008", familyId: "LTP_03", topic: "synaptic_plasticity", query: "Why must glutamate binding and postsynaptic depolarization occur together for strong NMDA current?", relevantIds: ["D003"], note: "Mechanism involving magnesium block.", queryType: "mechanism", difficulty: "hard" },
  { id: "Q009", familyId: "LTP_04", topic: "synaptic_plasticity", query: "How can a synapse become more responsive to later glutamate release after potentiation?", relevantIds: ["D004"], note: "Indirect AMPA-trafficking query.", queryType: "indirect", difficulty: "medium" },
  { id: "Q010", familyId: "LTP_05", topic: "synaptic_plasticity", query: "Which receptor mechanisms can initiate and then express stronger excitatory synaptic transmission?", relevantIds: ["D003", "D004"], note: "Multi-passage LTP mechanism.", queryType: "multi", difficulty: "hard" },

  { id: "Q011", familyId: "MIC_01", topic: "microglia", query: "Which resident immune cells survey the central nervous system?", relevantIds: ["D005"], note: "Direct microglia query.", queryType: "direct", difficulty: "easy" },
  { id: "Q012", familyId: "MIC_02", topic: "microglia", query: "What cells act as local immune sentinels within brain tissue?", relevantIds: ["D005"], note: "Semantic paraphrase with reduced exact vocabulary.", queryType: "paraphrase", difficulty: "medium" },
  { id: "Q013", familyId: "MIC_03", topic: "microglia", query: "How can CNS immune cells change their signaling after injury or infection?", relevantIds: ["D005"], note: "Context-dependent immune signaling.", queryType: "mechanism", difficulty: "medium" },
  { id: "Q014", familyId: "MIC_04", topic: "microglia", query: "Which cells can help remove or remodel synaptic connections during development?", relevantIds: ["D006"], note: "Indirect synaptic-pruning query.", queryType: "indirect", difficulty: "medium" },
  { id: "Q015", familyId: "MIC_05", topic: "microglia", query: "Which microglial functions span both immune surveillance and synaptic remodeling?", relevantIds: ["D005", "D006"], note: "Multi-passage microglia query.", queryType: "multi", difficulty: "hard" },

  { id: "Q016", familyId: "MYE_01", topic: "myelin", query: "Which cells form myelin in the central nervous system?", relevantIds: ["D007"], note: "Direct oligodendrocyte query.", queryType: "direct", difficulty: "easy" },
  { id: "Q017", familyId: "MYE_02", topic: "myelin", query: "What insulation around CNS axons helps electrical signals travel faster?", relevantIds: ["D007"], note: "Semantic paraphrase of myelin and conduction.", queryType: "paraphrase", difficulty: "medium" },
  { id: "Q018", familyId: "MYE_03", topic: "myelin", query: "Why can impulses move rapidly between nodes of Ranvier instead of depolarizing every membrane segment?", relevantIds: ["D007"], note: "Mechanistic saltatory-conduction query.", queryType: "mechanism", difficulty: "hard" },
  { id: "Q019", familyId: "MYE_04", topic: "myelin", query: "Which peripheral glial cell wraps an axon segment to support rapid conduction?", relevantIds: ["D008"], note: "PNS myelin query.", queryType: "indirect", difficulty: "medium" },
  { id: "Q020", familyId: "MYE_05", topic: "myelin", query: "Which glial cells provide myelin in the CNS versus the PNS?", relevantIds: ["D007", "D008"], note: "Cross-system multi-passage query.", queryType: "multi", difficulty: "hard" },

  { id: "Q021", familyId: "AST_01", topic: "astrocytes", query: "Which glial cells buffer extracellular potassium and remove glutamate near synapses?", relevantIds: ["D009"], note: "Direct astrocyte-homeostasis query.", queryType: "direct", difficulty: "easy" },
  { id: "Q022", familyId: "AST_02", topic: "astrocytes", query: "What support cells help neurons keep the chemical environment around synapses stable?", relevantIds: ["D009"], note: "Semantic paraphrase.", queryType: "paraphrase", difficulty: "medium" },
  { id: "Q023", familyId: "AST_03", topic: "astrocytes", query: "How can glia reduce excessive extracellular potassium and neurotransmitter accumulation?", relevantIds: ["D009"], note: "Mechanistic homeostasis query.", queryType: "mechanism", difficulty: "medium" },
  { id: "Q024", familyId: "AST_04", topic: "astrocytes", query: "Which neural support cells contact blood vessels and also provide metabolic support to neurons?", relevantIds: ["D010"], note: "Indirect vascular/metabolic query.", queryType: "indirect", difficulty: "medium" },
  { id: "Q025", familyId: "AST_05", topic: "astrocytes", query: "Which astrocyte roles span synaptic homeostasis, metabolism, and the neurovascular interface?", relevantIds: ["D009", "D010"], note: "Multi-passage astrocyte query.", queryType: "multi", difficulty: "hard" },

  { id: "Q026", familyId: "BBB_01", topic: "blood_brain_barrier", query: "What cellular structure forms the main physical barrier between blood and brain tissue?", relevantIds: ["D011"], note: "Direct BBB endothelial-junction query.", queryType: "direct", difficulty: "easy" },
  { id: "Q027", familyId: "BBB_02", topic: "blood_brain_barrier", query: "What keeps substances from freely leaking between neighboring brain capillary cells?", relevantIds: ["D011"], note: "Paraphrase of endothelial tight junctions.", queryType: "paraphrase", difficulty: "medium" },
  { id: "Q028", familyId: "BBB_03", topic: "blood_brain_barrier", query: "How does the BBB limit paracellular entry while still allowing selected molecules to cross?", relevantIds: ["D011", "D012"], note: "Mechanism combining tight junctions and selective transport.", queryType: "mechanism", difficulty: "hard" },
  { id: "Q029", familyId: "BBB_04", topic: "blood_brain_barrier", query: "Which supporting cell types participate with endothelium in the neurovascular unit?", relevantIds: ["D012"], note: "Indirect support-cell query.", queryType: "indirect", difficulty: "medium" },
  { id: "Q030", familyId: "BBB_05", topic: "blood_brain_barrier", query: "Which features together create selective blood-to-brain exchange?", relevantIds: ["D011", "D012"], note: "Multi-passage BBB query.", queryType: "multi", difficulty: "hard" },

  { id: "Q031", familyId: "DA_01", topic: "dopamine", query: "How is dopamine involved in reward prediction error?", relevantIds: ["D013"], note: "Direct reinforcement-learning query.", queryType: "direct", difficulty: "easy" },
  { id: "Q032", familyId: "DA_02", topic: "dopamine", query: "What signal helps update expectations when an outcome is better or worse than predicted?", relevantIds: ["D013"], note: "Semantic paraphrase with no dopamine term.", queryType: "paraphrase", difficulty: "medium" },
  { id: "Q033", familyId: "DA_03", topic: "dopamine", query: "Why is dopamine better described as contributing to reinforcement learning than as a simple pleasure chemical?", relevantIds: ["D013"], note: "Conceptual mechanism query.", queryType: "mechanism", difficulty: "hard" },
  { id: "Q034", familyId: "DA_04", topic: "dopamine", query: "Loss of which midbrain dopaminergic pathway is strongly linked to Parkinsonian motor symptoms?", relevantIds: ["D014"], note: "Indirect movement-pathway query.", queryType: "indirect", difficulty: "medium" },
  { id: "Q035", familyId: "DA_05", topic: "dopamine", query: "Which major dopamine functions in this dataset involve learning versus movement?", relevantIds: ["D013", "D014"], note: "Multi-passage dopamine query.", queryType: "multi", difficulty: "hard" },

  { id: "Q036", familyId: "GABA_01", topic: "gaba", query: "Which GABA receptor directly forms a chloride channel?", relevantIds: ["D015"], note: "Direct GABA-A query.", queryType: "direct", difficulty: "easy" },
  { id: "Q037", familyId: "GABA_02", topic: "gaba", query: "What receptor usually produces rapid inhibitory signaling by changing chloride conductance?", relevantIds: ["D015"], note: "Paraphrase of fast ionotropic inhibition.", queryType: "paraphrase", difficulty: "medium" },
  { id: "Q038", familyId: "GABA_03", topic: "gaba", query: "Why can opening a GABA-A receptor have different voltage effects if the chloride gradient changes?", relevantIds: ["D015"], note: "Mechanistic electrochemical-gradient query.", queryType: "mechanism", difficulty: "hard" },
  { id: "Q039", familyId: "GABA_04", topic: "gaba", query: "Which inhibitory GABA receptor works through G proteins rather than as an ion channel?", relevantIds: ["D016"], note: "Indirect metabotropic query.", queryType: "indirect", difficulty: "medium" },
  { id: "Q040", familyId: "GABA_05", topic: "gaba", query: "How do GABA-A and GABA-B receptors differ in speed and signaling mechanism?", relevantIds: ["D015", "D016"], note: "Multi-passage receptor comparison.", queryType: "multi", difficulty: "hard" },

  { id: "Q041", familyId: "5HT_01", topic: "serotonin", query: "Where are many serotonin-producing neurons located in the brain?", relevantIds: ["D017"], note: "Direct raphe-nuclei query.", queryType: "direct", difficulty: "easy" },
  { id: "Q042", familyId: "5HT_02", topic: "serotonin", query: "What brainstem nuclei send widespread serotonergic projections?", relevantIds: ["D017"], note: "Paraphrase of raphe projections.", queryType: "paraphrase", difficulty: "medium" },
  { id: "Q043", familyId: "5HT_03", topic: "serotonin", query: "How can one neurotransmitter influence many functions such as sleep, appetite, mood, and arousal?", relevantIds: ["D017", "D018"], note: "Mechanistic query spanning broad projections and receptor diversity.", queryType: "mechanism", difficulty: "hard" },
  { id: "Q044", familyId: "5HT_04", topic: "serotonin", query: "Which serotonin receptor is unusual because it is an ion channel rather than a GPCR?", relevantIds: ["D018"], note: "Indirect receptor-diversity query.", queryType: "indirect", difficulty: "medium" },
  { id: "Q045", familyId: "5HT_05", topic: "serotonin", query: "Which features of serotonin signaling support both broad brain influence and diverse cellular effects?", relevantIds: ["D017", "D018"], note: "Multi-passage serotonin query.", queryType: "multi", difficulty: "hard" },

  { id: "Q046", familyId: "CB_01", topic: "cerebellum", query: "What role does the cerebellum play in coordination and motor error correction?", relevantIds: ["D019"], note: "Direct cerebellar-function query.", queryType: "direct", difficulty: "easy" },
  { id: "Q047", familyId: "CB_02", topic: "cerebellum", query: "What structure helps compare intended movement with ongoing performance and adjust motor commands?", relevantIds: ["D019"], note: "Semantic paraphrase of cerebellar error correction.", queryType: "paraphrase", difficulty: "medium" },
  { id: "Q048", familyId: "CB_03", topic: "cerebellum", query: "How can comparing expected and actual movement-related signals support motor learning?", relevantIds: ["D019"], note: "Mechanistic learning query.", queryType: "mechanism", difficulty: "hard" },
  { id: "Q049", familyId: "CB_04", topic: "cerebellum", query: "Which inhibitory neuron provides the main output of cerebellar cortex?", relevantIds: ["D020"], note: "Indirect Purkinje-cell query.", queryType: "indirect", difficulty: "medium" },
  { id: "Q050", familyId: "CB_05", topic: "cerebellum", query: "Which cerebellar features in this dataset connect motor error correction with inhibitory cortical output?", relevantIds: ["D019", "D020"], note: "Multi-passage cerebellar query.", queryType: "multi", difficulty: "hard" },
];
