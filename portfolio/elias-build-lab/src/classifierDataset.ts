export type ClassLabel = "PASS" | "REVIEW" | "FAIL";
export type DataSplit = "train" | "validation" | "test";
export type ClassifierDifficulty = "easy" | "medium" | "hard";
export type ReviewStatus = "template_generated" | "human_reviewed";

export type ClassifierExample = {
  id: string;
  familyId: string;
  topic: string;
  concept: string;
  text: string;
  label: ClassLabel;
  rationale: string;
  difficulty: ClassifierDifficulty;
  failureMode: string;
  split: DataSplit;
  sourceType: "synthetic";
  reviewStatus: ReviewStatus;
  variant: 1 | 2;
};

type ConceptSeed = {
  topic: string;
  concept: string;
  pass: string;
  review: string;
  fail: string;
  passRationale: string;
  reviewRationale: string;
  failRationale: string;
  failureMode: string;
};

const CONCEPTS: ConceptSeed[] = [
  { topic: "action_potential", concept: "sodium_upstroke", pass: "Voltage-gated sodium channels open rapidly during the action-potential upstroke, allowing sodium influx that depolarizes the membrane.", review: "Sodium channels are important during action potentials.", fail: "Voltage-gated potassium channels create the rapid depolarizing upstroke by carrying sodium into the neuron.", passRationale: "Correctly links sodium-channel opening and sodium influx to rapid depolarization.", reviewRationale: "Broadly true but too underspecified to demonstrate mechanism.", failRationale: "Assigns the sodium-mediated upstroke to potassium channels.", failureMode: "wrong_mechanism" },
  { topic: "action_potential", concept: "potassium_repolarization", pass: "Delayed opening of voltage-gated potassium channels contributes to repolarization as potassium leaves the neuron.", review: "Potassium is involved after a neuron depolarizes.", fail: "Repolarization is driven mainly by potassium moving into the neuron through voltage-gated potassium channels.", passRationale: "Correctly identifies delayed potassium-channel opening and outward potassium current.", reviewRationale: "Direction and channel mechanism are missing.", failRationale: "Reverses the direction of potassium movement.", failureMode: "reversed_direction" },
  { topic: "action_potential", concept: "absolute_refractory", pass: "The absolute refractory period largely reflects voltage-gated sodium-channel inactivation, which temporarily prevents another full action potential.", review: "A neuron needs some recovery time before it can fire normally again.", fail: "The absolute refractory period occurs because all voltage-gated sodium channels remain fully available immediately after a spike.", passRationale: "Correctly ties absolute refractoriness to sodium-channel inactivation.", reviewRationale: "Describes the phenomenon without its key mechanism.", failRationale: "States the opposite of sodium-channel inactivation.", failureMode: "reversed_direction" },
  { topic: "action_potential", concept: "all_or_none", pass: "Once threshold is reached, a typical action potential is all-or-none; stronger suprathreshold input usually changes firing frequency rather than making each spike proportionally taller.", review: "Threshold affects whether a neuron fires an action potential.", fail: "Above threshold, stronger inputs make each individual action potential proportionally larger in amplitude.", passRationale: "Correctly distinguishes spike amplitude from firing-rate coding.", reviewRationale: "Correct but incomplete about all-or-none behavior.", failRationale: "Treats action-potential amplitude as graded above threshold.", failureMode: "overgeneralization" },
  { topic: "action_potential", concept: "axon_propagation", pass: "Local current from an active axonal segment depolarizes adjacent membrane and recruits nearby voltage-gated channels, allowing the action potential to propagate.", review: "Action potentials move along axons by electrical activity in the membrane.", fail: "An action potential propagates because the same sodium ions physically travel from the cell body to the axon terminal.", passRationale: "Correctly describes regenerative propagation through local current and channel recruitment.", reviewRationale: "Too vague to distinguish regenerative propagation from passive current flow.", failRationale: "Incorrectly treats ion particles as carrying the spike down the entire axon.", failureMode: "wrong_mechanism" },

  { topic: "synaptic_plasticity", concept: "nmda_coincidence", pass: "NMDA receptors require glutamate binding and sufficient postsynaptic depolarization to relieve magnesium block and permit substantial ion flow.", review: "NMDA receptors are involved in excitatory synaptic plasticity.", fail: "NMDA receptors open maximally whenever glutamate binds, regardless of postsynaptic voltage or magnesium block.", passRationale: "Correctly describes ligand and voltage dependence.", reviewRationale: "Broadly correct but omits the coincidence-detection mechanism.", failRationale: "Removes the voltage-dependent magnesium-block requirement.", failureMode: "wrong_mechanism" },
  { topic: "synaptic_plasticity", concept: "calcium_ltp", pass: "Calcium entry through active NMDA receptors can trigger intracellular signaling that contributes to long-term potentiation.", review: "Calcium can matter for synaptic strengthening.", fail: "Long-term potentiation requires calcium to leave the postsynaptic neuron through NMDA receptors.", passRationale: "Correctly links NMDA-mediated calcium entry to LTP signaling.", reviewRationale: "Direction, receptor, and downstream role are underspecified.", failRationale: "Reverses the direction of calcium movement.", failureMode: "reversed_direction" },
  { topic: "synaptic_plasticity", concept: "ampa_trafficking", pass: "One expression mechanism for LTP is increased insertion or stabilization of AMPA receptors at the postsynaptic membrane.", review: "AMPA receptors can change during synaptic plasticity.", fail: "LTP is expressed by permanently removing AMPA receptors from the postsynaptic membrane.", passRationale: "Correctly identifies a common postsynaptic expression mechanism for LTP.", reviewRationale: "Too broad to show whether receptor number rises or falls.", failRationale: "Reverses a common LTP-associated AMPA-receptor change.", failureMode: "reversed_direction" },
  { topic: "synaptic_plasticity", concept: "ltd", pass: "Long-term depression can involve signaling that reduces synaptic efficacy, including decreased postsynaptic AMPA-receptor contribution in some forms.", review: "Long-term depression weakens synaptic transmission.", fail: "Long-term depression always increases postsynaptic AMPA-receptor number and strengthens the synapse.", passRationale: "Accurately describes LTD without claiming one universal mechanism.", reviewRationale: "Correct direction but mechanism and context are absent.", failRationale: "Reverses the functional direction and overstates universality.", failureMode: "unsupported_certainty" },
  { topic: "synaptic_plasticity", concept: "plasticity_context", pass: "The direction and mechanism of synaptic plasticity depend on circuit, timing, receptor state, and stimulation pattern rather than one universal rule.", review: "Synapses can become stronger or weaker depending on activity.", fail: "Every excitatory synapse uses the same molecular rule to determine whether activity produces LTP or LTD.", passRationale: "Preserves context dependence and avoids universal claims.", reviewRationale: "Broadly true but omits the variables that shape plasticity.", failRationale: "Claims a universal mechanism across excitatory synapses.", failureMode: "unsupported_certainty" },

  { topic: "microglia", concept: "resident_immune", pass: "Microglia are resident immune cells of the central nervous system that survey their local environment and respond to injury or infection.", review: "Microglia are involved in immune activity in the brain.", fail: "Microglia are circulating red blood cells that enter healthy brain tissue to provide routine immune surveillance.", passRationale: "Correctly identifies microglia as resident CNS immune cells.", reviewRationale: "Broadly correct but lacks residency and surveillance detail.", failRationale: "Misclassifies microglia as circulating erythrocytes.", failureMode: "category_error" },
  { topic: "microglia", concept: "context_activation", pass: "Microglial responses are context dependent and can include inflammatory, regulatory, reparative, or phagocytic functions.", review: "Activated microglia can release signaling molecules.", fail: "Activated microglia are always harmful and have only one inflammatory state.", passRationale: "Accurately represents functional heterogeneity.", reviewRationale: "True but too narrow to capture context dependence.", failRationale: "Uses an unsupported universal harmful-state claim.", failureMode: "unsupported_certainty" },
  { topic: "microglia", concept: "synaptic_pruning", pass: "Microglia can participate in developmental synaptic remodeling and pruning, including through interactions with complement-related pathways.", review: "Microglia can affect synapses during development.", fail: "Microglia build new myelin sheaths around CNS axons as their main role in synaptic pruning.", passRationale: "Correctly links microglia to developmental synaptic remodeling.", reviewRationale: "Broadly true but lacks a mechanism.", failRationale: "Confuses microglial pruning with oligodendrocyte myelination.", failureMode: "category_error" },
  { topic: "microglia", concept: "phagocytosis", pass: "Microglia can engulf cellular debris and other material through phagocytic processes, especially after tissue injury.", review: "Microglia can help clean up damaged tissue.", fail: "Microglia remove debris primarily by secreting antibodies that dissolve injured neurons.", passRationale: "Correctly identifies phagocytosis as a microglial function.", reviewRationale: "Correct but informal and mechanistically sparse.", failRationale: "Invents antibody secretion as the primary debris-removal mechanism.", failureMode: "wrong_mechanism" },
  { topic: "microglia", concept: "cytokine_context", pass: "Cytokines released by microglia can have different effects depending on the molecule, timing, concentration, and cellular context.", review: "Microglial cytokines can influence nearby cells.", fail: "Every cytokine released by microglia has the same effect on every nearby cell.", passRationale: "Correctly preserves cytokine and context heterogeneity.", reviewRationale: "True but lacks conditions or examples.", failRationale: "Makes an unsupported universal claim.", failureMode: "unsupported_certainty" },

  { topic: "myelin", concept: "oligodendrocyte_cns", pass: "Oligodendrocytes form myelin around axons in the central nervous system.", review: "Oligodendrocytes support axons in the CNS.", fail: "Schwann cells are the primary cells that form myelin around axons throughout the central nervous system.", passRationale: "Correctly identifies the CNS myelinating cell.", reviewRationale: "Broadly true but omits the defining myelination function.", failRationale: "Substitutes the PNS myelinating cell for the CNS cell.", failureMode: "wrong_anatomy" },
  { topic: "myelin", concept: "schwann_pns", pass: "Schwann cells form myelin around peripheral axons and typically myelinate one axonal segment per myelinating cell.", review: "Schwann cells support peripheral nerves.", fail: "Oligodendrocytes are the exclusive myelinating cells of peripheral nerves.", passRationale: "Correctly identifies Schwann-cell myelination in the PNS.", reviewRationale: "Correct but does not distinguish myelinating function.", failRationale: "Assigns PNS myelination exclusively to oligodendrocytes.", failureMode: "wrong_anatomy" },
  { topic: "myelin", concept: "saltatory_conduction", pass: "Myelin supports saltatory conduction by electrically insulating internodes so action potentials are regenerated mainly at nodes of Ranvier.", review: "Myelin makes nerve conduction faster.", fail: "Myelin speeds conduction by causing action potentials to be generated continuously at every point along the insulated internode.", passRationale: "Correctly links myelin and nodal regeneration.", reviewRationale: "Correct outcome but omits saltatory mechanism.", failRationale: "Reverses the nodal pattern of regeneration.", failureMode: "wrong_mechanism" },
  { topic: "myelin", concept: "membrane_properties", pass: "Myelination increases effective membrane resistance and reduces capacitance across internodes, helping current spread farther and charge the membrane faster.", review: "Myelin changes the electrical properties of the axonal membrane.", fail: "Myelin accelerates conduction mainly by greatly increasing internodal membrane capacitance.", passRationale: "Correctly describes key passive electrical effects of myelin.", reviewRationale: "Correct but lacks direction of electrical changes.", failRationale: "States the opposite capacitance effect.", failureMode: "reversed_direction" },
  { topic: "myelin", concept: "nodes_sodium_channels", pass: "Nodes of Ranvier contain high densities of voltage-gated sodium channels that support regenerative action-potential conduction.", review: "Nodes of Ranvier are important for myelinated axons.", fail: "Nodes of Ranvier are gaps where voltage-gated sodium channels are absent so current cannot be regenerated.", passRationale: "Correctly identifies nodal sodium-channel enrichment.", reviewRationale: "Correct but mechanistically incomplete.", failRationale: "Reverses the key channel distribution at nodes.", failureMode: "reversed_direction" },

  { topic: "astrocytes", concept: "potassium_buffering", pass: "Astrocytes help regulate extracellular potassium, limiting disruptive changes in neuronal excitability.", review: "Astrocytes help maintain the environment around neurons.", fail: "Astrocytes normally increase extracellular potassium without limit to make neurons easier to excite.", passRationale: "Correctly identifies potassium homeostasis as an astrocyte function.", reviewRationale: "Broadly true but not specific enough to demonstrate the mechanism.", failRationale: "Reverses the homeostatic role and adds an unsupported purpose.", failureMode: "reversed_direction" },
  { topic: "astrocytes", concept: "glutamate_uptake", pass: "Astrocytic transporters remove extracellular glutamate and help limit excessive excitatory signaling.", review: "Astrocytes participate in glutamate handling.", fail: "Astrocytes maintain normal synaptic function mainly by preventing all glutamate uptake from the extracellular space.", passRationale: "Correctly describes astrocytic glutamate clearance.", reviewRationale: "Correct but direction and consequence are missing.", failRationale: "Reverses glutamate uptake.", failureMode: "reversed_direction" },
  { topic: "astrocytes", concept: "metabolic_support", pass: "Astrocytes provide metabolic support to neurons and participate in local energy-substrate handling.", review: "Astrocytes can support neuronal metabolism.", fail: "Astrocytes cannot participate in neuronal metabolic support because they only provide structural scaffolding.", passRationale: "Correctly recognizes a metabolic-support role.", reviewRationale: "True but underspecified.", failRationale: "Incorrectly excludes metabolic functions.", failureMode: "category_error" },
  { topic: "astrocytes", concept: "vascular_endfeet", pass: "Astrocytic endfeet contact cerebral blood vessels and participate in neurovascular signaling and homeostatic regulation.", review: "Astrocytes interact with brain blood vessels.", fail: "Astrocytes form the vascular lumen and replace endothelial cells in cerebral capillaries.", passRationale: "Correctly describes astrocyte-vessel contact without replacing endothelial identity.", reviewRationale: "Correct but does not specify the role of endfeet.", failRationale: "Confuses astrocytes with vascular endothelial cells.", failureMode: "category_error" },
  { topic: "astrocytes", concept: "bbb_support", pass: "Astrocytes support blood-brain barrier function, but the main physical tight-junction barrier is formed by brain endothelial cells.", review: "Astrocytes are involved in the blood-brain barrier.", fail: "Astrocytes themselves form the principal endothelial tight-junction seal of the blood-brain barrier.", passRationale: "Correctly separates astrocyte support from the endothelial barrier.", reviewRationale: "Broadly true but may blur which cell forms the physical barrier.", failRationale: "Misidentifies the tight-junction-forming cell type.", failureMode: "category_error" },

  { topic: "blood_brain_barrier", concept: "tight_junctions", pass: "Specialized brain endothelial cells form tight junctions that strongly restrict paracellular movement across the blood-brain barrier.", review: "Tight junctions are important at the blood-brain barrier.", fail: "The blood-brain barrier depends on large gaps between endothelial cells that promote unrestricted paracellular diffusion.", passRationale: "Correctly identifies endothelial tight junctions and their restrictive role.", reviewRationale: "Correct but lacks cell type and functional direction.", failRationale: "Reverses the structural basis of barrier restriction.", failureMode: "reversed_direction" },
  { topic: "blood_brain_barrier", concept: "selective_transport", pass: "Blood-brain barrier endothelial cells use selective transport systems to permit controlled exchange of specific nutrients and molecules.", review: "Some substances cross the blood-brain barrier more readily than others.", fail: "An intact blood-brain barrier blocks every molecule, including oxygen and essential nutrients, from entering brain tissue.", passRationale: "Correctly preserves selective rather than absolute barrier function.", reviewRationale: "True but does not describe transport mechanisms.", failRationale: "Treats the barrier as completely impermeable.", failureMode: "overgeneralization" },
  { topic: "blood_brain_barrier", concept: "pericytes", pass: "Pericytes are part of the neurovascular unit and contribute to vascular stability and blood-brain barrier regulation.", review: "Pericytes interact with brain microvessels.", fail: "Pericytes are neurons whose main role is to conduct action potentials across the blood-brain barrier.", passRationale: "Correctly places pericytes in the neurovascular unit.", reviewRationale: "Correct but too vague about function.", failRationale: "Misclassifies pericytes as neurons.", failureMode: "category_error" },
  { topic: "blood_brain_barrier", concept: "astrocyte_endfeet_support", pass: "Astrocytic endfeet help regulate the neurovascular environment and support blood-brain barrier properties without being the endothelial tight-junction layer.", review: "Astrocyte endfeet are associated with the blood-brain barrier.", fail: "Astrocytic endfeet replace endothelial cells as the blood-contacting surface of brain capillaries.", passRationale: "Correctly describes a supportive role and preserves vascular anatomy.", reviewRationale: "Association is true but functional and anatomical details are missing.", failRationale: "Reverses cellular organization of the vessel wall.", failureMode: "wrong_anatomy" },
  { topic: "blood_brain_barrier", concept: "barrier_context", pass: "Blood-brain barrier permeability can change with region, transporter activity, inflammation, and disease rather than remaining fixed in every condition.", review: "The blood-brain barrier can change under some conditions.", fail: "Blood-brain barrier permeability is identical in every brain region and cannot change during inflammation or disease.", passRationale: "Correctly represents dynamic and regional variation.", reviewRationale: "True but lacks the factors that change permeability.", failRationale: "Makes an unsupported fixed-barrier claim.", failureMode: "unsupported_certainty" },

  { topic: "dopamine", concept: "reward_prediction_error", pass: "Midbrain dopamine activity can encode reward prediction error, helping update expectations when outcomes differ from predictions.", review: "Dopamine is involved in reward-related learning.", fail: "Dopamine neurons only signal whether an experience feels pleasant and do not participate in updating predictions.", passRationale: "Correctly describes a major reinforcement-learning role.", reviewRationale: "Broadly true but omits prediction error.", failRationale: "Reduces dopamine to pleasure and denies learning-related signaling.", failureMode: "overgeneralization" },
  { topic: "dopamine", concept: "not_pleasure_only", pass: "Dopamine contributes to motivation, learning, movement, and other functions, so describing it as only a pleasure chemical is misleading.", review: "Dopamine has several roles in the brain.", fail: "Dopamine has one biological function: directly producing pleasure whenever it is released.", passRationale: "Correctly rejects a single-function pleasure model.", reviewRationale: "Correct but does not identify the relevant functions.", failRationale: "Makes a single-function universal claim.", failureMode: "unsupported_certainty" },
  { topic: "dopamine", concept: "nigrostriatal_movement", pass: "Nigrostriatal dopamine modulates basal-ganglia circuits involved in movement, and loss of substantia nigra dopaminergic neurons is central to Parkinson disease.", review: "Dopamine is important for movement.", fail: "Parkinsonian motor symptoms primarily result from excessive growth of nigrostriatal dopamine neurons.", passRationale: "Correctly links dopamine loss in the nigrostriatal system to Parkinsonian movement dysfunction.", reviewRationale: "True but anatomically and mechanistically incomplete.", failRationale: "Reverses the direction of the Parkinson-related neuronal change.", failureMode: "reversed_direction" },
  { topic: "dopamine", concept: "pathway_diversity", pass: "Different dopaminergic pathways support different functions, so mesolimbic, mesocortical, nigrostriatal, and tuberoinfundibular signaling should not be treated as interchangeable.", review: "Dopamine pathways can have different functions.", fail: "All dopamine pathways project to the same targets and perform the same function.", passRationale: "Correctly preserves pathway-specific anatomy and function.", reviewRationale: "True but lacks examples or implications.", failRationale: "Collapses distinct pathways into one.", failureMode: "overgeneralization" },
  { topic: "dopamine", concept: "receptor_diversity", pass: "Dopamine receptors belong to multiple receptor families with different intracellular signaling effects, so dopamine does not produce one uniform cellular response.", review: "Dopamine receptors can signal differently.", fail: "Every dopamine receptor has identical signaling and produces the same effect in every cell.", passRationale: "Correctly represents receptor and cell-context diversity.", reviewRationale: "True but underspecified.", failRationale: "Makes a universal identical-response claim.", failureMode: "unsupported_certainty" },

  { topic: "gaba", concept: "gabaa_ionotropic", pass: "GABA-A receptors are ionotropic ligand-gated chloride channels that usually mediate fast inhibitory synaptic effects in the mature CNS.", review: "GABA-A receptors are involved in inhibition.", fail: "GABA-A receptors are slow G-protein-coupled receptors that inhibit cells only through second-messenger cascades.", passRationale: "Correctly identifies receptor class, ion, and typical time course.", reviewRationale: "Broadly true but lacks receptor mechanism.", failRationale: "Confuses GABA-A with metabotropic GABA-B signaling.", failureMode: "category_error" },
  { topic: "gaba", concept: "gabab_metabotropic", pass: "GABA-B receptors are metabotropic G-protein-coupled receptors that can modulate potassium and calcium channels and produce slower inhibitory effects.", review: "GABA-B receptors can inhibit neural activity.", fail: "GABA-B receptors are chloride-permeable ion channels that mediate the fastest inhibitory postsynaptic currents.", passRationale: "Correctly identifies metabotropic GABA-B signaling.", reviewRationale: "Correct but mechanistically incomplete.", failRationale: "Confuses GABA-B with GABA-A.", failureMode: "category_error" },
  { topic: "gaba", concept: "chloride_gradient", pass: "The voltage effect of opening GABA-A channels depends on the chloride electrochemical gradient, so GABA-A is not intrinsically hyperpolarizing in every cell and developmental state.", review: "Chloride levels influence GABA-A effects.", fail: "Opening GABA-A receptors always hyperpolarizes every neuron regardless of intracellular chloride concentration.", passRationale: "Correctly preserves gradient dependence.", reviewRationale: "True but lacks the electrochemical mechanism.", failRationale: "Uses an unsupported universal claim.", failureMode: "unsupported_certainty" },
  { topic: "gaba", concept: "fast_slow_inhibition", pass: "GABA-A signaling is generally faster because it directly gates an ion channel, whereas GABA-B signaling is slower because it uses G-protein pathways.", review: "GABA-A and GABA-B inhibition have different time courses.", fail: "GABA-B signaling is always faster than GABA-A because GPCR cascades open instantly without intermediates.", passRationale: "Correctly contrasts ionotropic and metabotropic time courses.", reviewRationale: "Correct comparison but without mechanism.", failRationale: "Reverses typical kinetics and misstates GPCR signaling.", failureMode: "wrong_mechanism" },
  { topic: "gaba", concept: "presynaptic_gabab", pass: "Presynaptic GABA-B receptors can reduce neurotransmitter release by modulating calcium-channel activity and release machinery.", review: "GABA-B receptors can act presynaptically.", fail: "Presynaptic GABA-B activation necessarily increases calcium entry and boosts transmitter release at every synapse.", passRationale: "Correctly describes a common inhibitory presynaptic effect.", reviewRationale: "Correct but omits the functional consequence.", failRationale: "Reverses the common effect on calcium entry and transmitter release.", failureMode: "reversed_direction" },

  { topic: "serotonin", concept: "raphe_location", pass: "Many serotonin-producing neurons are located in brainstem raphe nuclei and project broadly through the nervous system.", review: "Serotonin neurons are found in the brainstem.", fail: "Most central serotonin-producing neurons are located exclusively in the cerebellar cortex and do not project broadly.", passRationale: "Correctly identifies raphe nuclei and widespread projections.", reviewRationale: "Broadly correct but omits the raphe and projection pattern.", failRationale: "Places central serotonergic neurons in the wrong structure.", failureMode: "wrong_anatomy" },
  { topic: "serotonin", concept: "broad_functions", pass: "Serotonergic signaling can influence mood, arousal, sleep, appetite, and other functions, with effects depending on receptor and circuit context.", review: "Serotonin affects several behaviors and physiological functions.", fail: "Serotonin has one fixed behavioral effect that is identical across all receptors and brain regions.", passRationale: "Correctly preserves functional and receptor/circuit diversity.", reviewRationale: "True but lacks context dependence.", failRationale: "Makes an unsupported uniform-effect claim.", failureMode: "unsupported_certainty" },
  { topic: "serotonin", concept: "5ht3_ion_channel", pass: "The 5-HT3 receptor is unusual among serotonin receptors because it is a ligand-gated ion channel.", review: "5-HT3 is different from many other serotonin receptors.", fail: "5-HT3 is a classic G-protein-coupled serotonin receptor with no ion-channel function.", passRationale: "Correctly identifies 5-HT3 as ionotropic.", reviewRationale: "Correct but does not specify the distinction.", failRationale: "Misclassifies 5-HT3 as a GPCR.", failureMode: "category_error" },
  { topic: "serotonin", concept: "gpcr_majority", pass: "Most serotonin receptor families are G-protein-coupled receptors, while 5-HT3 is the major ionotropic exception.", review: "Many serotonin receptors use metabotropic signaling.", fail: "Every serotonin receptor is a ligand-gated ion channel.", passRationale: "Correctly describes the dominant receptor architecture and exception.", reviewRationale: "Broadly true but lacks the exception.", failRationale: "Incorrectly makes all serotonin receptors ionotropic.", failureMode: "overgeneralization" },
  { topic: "serotonin", concept: "not_happiness_only", pass: "Calling serotonin a simple happiness chemical is misleading because serotonergic circuits and receptor subtypes participate in many distinct functions.", review: "Serotonin is related to mood but does more than that.", fail: "Serotonin release directly determines happiness in the same way in every person and neural circuit.", passRationale: "Correctly rejects an oversimplified single-emotion model.", reviewRationale: "Broadly correct but lacks circuit and receptor context.", failRationale: "Makes a deterministic universal claim about subjective state.", failureMode: "unsupported_certainty" },

  { topic: "cerebellum", concept: "error_correction", pass: "The cerebellum contributes to motor coordination and learning by using sensory and motor-related information to reduce movement errors over time.", review: "The cerebellum helps coordinate movement.", fail: "The cerebellum controls movement only by directly activating skeletal muscle fibers without comparing sensory or motor signals.", passRationale: "Correctly includes coordination, learning, and error-related processing.", reviewRationale: "True but omits learning and error correction.", failRationale: "Invents direct muscle activation and removes integrative processing.", failureMode: "wrong_mechanism" },
  { topic: "cerebellum", concept: "purkinje_output", pass: "Purkinje cells are inhibitory GABAergic neurons and form the principal output of the cerebellar cortex to deep cerebellar and vestibular nuclei.", review: "Purkinje cells are important output neurons in the cerebellum.", fail: "Purkinje cells are excitatory glutamatergic neurons that provide the main output from deep cerebellar nuclei to the cortex.", passRationale: "Correctly identifies transmitter, sign, and anatomical level of Purkinje output.", reviewRationale: "Broadly correct but lacks inhibitory identity and target.", failRationale: "Reverses transmitter, sign, and output anatomy.", failureMode: "wrong_anatomy" },
  { topic: "cerebellum", concept: "climbing_fibers", pass: "Climbing fibers arise from the inferior olive and provide powerful excitatory input to Purkinje cells.", review: "Climbing fibers strongly influence Purkinje cells.", fail: "Climbing fibers arise primarily from Purkinje cells and inhibit the inferior olive.", passRationale: "Correctly describes the origin and direction of climbing-fiber input.", reviewRationale: "True but lacks origin and excitatory direction.", failRationale: "Reverses pathway origin and direction.", failureMode: "wrong_anatomy" },
  { topic: "cerebellum", concept: "mossy_parallel_path", pass: "Mossy fibers excite granule cells, whose parallel fibers then contact Purkinje-cell dendrites and other cerebellar cortical neurons.", review: "Mossy fibers influence Purkinje cells through cerebellar circuitry.", fail: "Mossy fibers bypass granule cells entirely and are the axons of Purkinje cells.", passRationale: "Correctly identifies the granule-cell/parallel-fiber relay.", reviewRationale: "Broadly correct but omits the relay.", failRationale: "Eliminates the granule-cell pathway and misidentifies fiber origin.", failureMode: "wrong_anatomy" },
  { topic: "cerebellum", concept: "motor_learning", pass: "Cerebellar plasticity contributes to adapting movements when repeated sensory feedback shows a mismatch between expected and actual outcomes.", review: "The cerebellum can learn from movement errors.", fail: "Cerebellar motor learning does not use sensory feedback and cannot change with repeated practice.", passRationale: "Correctly links feedback, error, and adaptation.", reviewRationale: "Correct but lacks the adaptation mechanism.", failRationale: "Denies feedback-dependent learning.", failureMode: "wrong_mechanism" },
];

const SHARED_WRAPPERS = [
  (text: string) => text,
  (text: string) => `Neuroscience statement: ${text}`,
];

function splitForConcept(indexWithinTopic: number): DataSplit {
  if (indexWithinTopic <= 2) return "train";
  if (indexWithinTopic === 3) return "validation";
  return "test";
}

function difficultyForConcept(indexWithinTopic: number): ClassifierDifficulty {
  return (["easy", "medium", "hard", "medium", "hard"] as ClassifierDifficulty[])[
    indexWithinTopic
  ];
}

export function buildClassifierDataset(): ClassifierExample[] {
  const perTopicIndex = new Map<string, number>();
  const rows: ClassifierExample[] = [];
  let familyCounter = 0;

  for (const seed of CONCEPTS) {
    const topicIndex = perTopicIndex.get(seed.topic) ?? 0;
    perTopicIndex.set(seed.topic, topicIndex + 1);
    familyCounter += 1;

    const familyId = `F${String(familyCounter).padStart(3, "0")}`;
    const split = splitForConcept(topicIndex);
    const difficulty = difficultyForConcept(topicIndex);

    const definitions: Array<{
      label: ClassLabel;
      core: string;
      rationale: string;
      failureMode: string;
    }> = [
      {
        label: "PASS",
        core: seed.pass,
        rationale: seed.passRationale,
        failureMode: "none",
      },
      {
        label: "REVIEW",
        core: seed.review,
        rationale: seed.reviewRationale,
        failureMode: "underspecified",
      },
      {
        label: "FAIL",
        core: seed.fail,
        rationale: seed.failRationale,
        failureMode: seed.failureMode,
      },
    ];

    for (const definition of definitions) {
      SHARED_WRAPPERS.forEach((wrapper, wrapperIndex) => {
        rows.push({
          id: `C${String(rows.length + 1).padStart(3, "0")}`,
          familyId,
          topic: seed.topic,
          concept: seed.concept,
          text: wrapper(definition.core),
          label: definition.label,
          rationale: definition.rationale,
          difficulty,
          failureMode: definition.failureMode,
          split,
          sourceType: "synthetic",
          reviewStatus: "template_generated",
          variant: (wrapperIndex + 1) as 1 | 2,
        });
      });
    }
  }

  return rows;
}

export const CLASSIFIER_DATASET = buildClassifierDataset();
