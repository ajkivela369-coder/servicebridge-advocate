import type { SubmissionBrief } from './submissionPdf';

export const syntheticSubmissionDemo: SubmissionBrief = {
    demo: true,
    title: 'Synthetic Evidence Integrity Demonstration',
    subtitle: 'Fictional records | Public portfolio demonstration | No real claimant data',
    requestedAction: 'Demonstrate a reviewer-ready evidence brief in which every material proposition traces to a fictional source and pinpoint page.',
    executiveArgument: 'The fictional record shows a consistent progression from a documented training injury to objective testing and sustained functional limitation. The packet separates objective findings, reported symptoms, medical reasoning, and administrative context while preserving a visible reconciliation note where the record is not perfectly uniform.',
    evidenceConvergence: [
        { evidence: 'Contemporaneous training note documents an acute shoulder and neck event.', establishes: 'A time-linked event is present in the fictional service record.', whyItMatters: 'Anchors chronology without inferring medical causation beyond the record.', source: '[Synthetic_Service_Record.pdf | page 3]' },
        { evidence: 'Electrodiagnostic report describes mild chronic denervation.', establishes: 'An objective neurologic finding is documented.', whyItMatters: 'Provides objective evidence separate from symptom report.', source: '[Synthetic_EMG_Report.pdf | page 2]' },
        { evidence: 'Functional evaluation documents reduced sitting tolerance and unscheduled recovery periods.', establishes: 'Sustained-work reliability is materially limited in the fictional record.', whyItMatters: 'Connects impairment evidence to function without overstating diagnosis.', source: '[Synthetic_Functional_Evaluation.pdf | pages 4-5]' },
    ],
    arguments: [
        {
            heading: 'Chronology is supported by independent record types',
            proposition: 'The fictional event, later objective testing, and functional evaluation form a traceable longitudinal sequence.',
            recordSupport: 'Training documentation, electrodiagnostic testing, and a separate functional evaluation each support a different part of the chronology.',
            medicalReasoning: 'The packet does not treat temporal sequence alone as proof of causation; it presents the records for reviewer reconciliation.',
            legalReasoning: 'The demonstration focuses on source integrity rather than a real legal conclusion.',
            sourceCitations: ['[Synthetic_Service_Record.pdf | page 3]', '[Synthetic_EMG_Report.pdf | page 2]', '[Synthetic_Functional_Evaluation.pdf | pages 4-5]'],
            authorityCitations: [],
        },
        {
            heading: 'Functional impact is separately documented',
            proposition: 'The fictional functional evaluation identifies limits relevant to sustained attendance, pace, and recovery.',
            recordSupport: 'The evaluator records sitting intolerance and the need for unscheduled recovery periods.',
            medicalReasoning: 'Functional observations are presented as documented findings, not as a new diagnosis.',
            legalReasoning: 'No real benefit entitlement is asserted in this synthetic demonstration.',
            sourceCitations: ['[Synthetic_Functional_Evaluation.pdf | pages 4-5]'],
            authorityCitations: [],
        },
    ],
    recordReconciliations: [
        {
            issue: 'One routine follow-up note described a normal brief office examination despite the later functional limitations.',
            favorableEvidence: 'The later evaluation measured sustained-task limitations over a longer observation window.',
            limitingContext: 'The packet does not portray the brief normal examination as nonexistent; it explains that the records measured different things at different times.',
            sourceCitations: ['[Synthetic_Clinic_Followup.pdf | page 1]', '[Synthetic_Functional_Evaluation.pdf | pages 4-5]'],
        },
    ],
    functionalCase: [
        'Fictional evaluation: sitting tolerance declines during sustained testing and requires position changes.',
        'Fictional evaluation: recovery periods are not fully predictable, affecting schedule reliability.',
    ],
    chronology: [
        { date: '2024-02-12', event: 'Training event documented.', source: '[Synthetic_Service_Record.pdf | page 3]', significance: 'Chronology anchor.' },
        { date: '2024-06-21', event: 'Electrodiagnostic testing completed.', source: '[Synthetic_EMG_Report.pdf | page 2]', significance: 'Objective test evidence.' },
        { date: '2025-01-15', event: 'Functional evaluation completed.', source: '[Synthetic_Functional_Evaluation.pdf | pages 4-5]', significance: 'Sustained-function evidence.' },
    ],
    objectiveFindings: [
        'Mild chronic denervation is documented in the fictional electrodiagnostic report [Synthetic_EMG_Report.pdf | page 2].',
        'Observed position changes and recovery periods are documented in the fictional functional evaluation [Synthetic_Functional_Evaluation.pdf | pages 4-5].',
    ],
    focusedQuestions: ['Would any reviewer need the complete fictional testing protocol or an additional longitudinal functional observation before relying on the sustained-work conclusion?'],
    medicalLiterature: [],
    requestedDisposition: 'Portfolio demonstration only: show that a finished evidence product can remain concise while retaining pinpoint provenance and visible reconciliation.',
    legalAuthorities: [],
    sourceAppendix: [
        { sourceId: 'S1', name: 'Synthetic_Service_Record.pdf', locator: 'Page 3', use: 'Pinpoint-cited fictional service evidence' },
        { sourceId: 'S2', name: 'Synthetic_EMG_Report.pdf', locator: 'Page 2', use: 'Pinpoint-cited fictional objective testing' },
        { sourceId: 'S3', name: 'Synthetic_Functional_Evaluation.pdf', locator: 'Pages 4-5', use: 'Pinpoint-cited fictional functional evidence' },
        { sourceId: 'S4', name: 'Synthetic_Clinic_Followup.pdf', locator: 'Page 1', use: 'Fictional reconciliation context' },
    ],
    preflight: { status: 'Ready to Submit', blockers: [], warnings: ['Synthetic portfolio demonstration only; not for agency filing.'] },
    citationAudit: { total: 10, pinpoint: 10, broad: 0, invalid: [], unresolved: [] },
    verificationNote: 'Synthetic demonstration. No real person, claim, diagnosis, provider, or agency determination is represented. All cited filenames and pages are fictional.',
};
