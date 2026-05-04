// Single source of truth for all legal/medical disclaimer copy.
// Edits made here propagate to the consent gate, footer, static pages,
// payment acknowledgments, and PDF reports.
// Source: docs/Legal Terms & Conditions.md

export const LEGAL_VERSION = '2026-04-30';
export const ENTITY_NAME = 'International ABA Institute LLC';
export const PRODUCT_NAME = 'BEST Galaxy\u2122';

export const SHORT_DISCLAIMER =
  `${PRODUCT_NAME} provides educational insights into executive functioning ` +
  'and behavior patterns. It is not a medical or mental health diagnostic ' +
  'tool. Please consult a licensed professional for clinical concerns.';

export const INLINE_DISCLAIMER =
  'Educational insights only. Not medical or mental health advice.';

export const PAYMENT_ACK =
  'By purchasing, you acknowledge this is an educational product and not a clinical service.';

export const FULL_DISCLAIMER_TITLE = 'Legal & Medical Disclaimer';

export const FULL_DISCLAIMER_BODY = [
  `The ${PRODUCT_NAME}, including all assessments, reports, interpretations, and recommendations ` +
    `provided by ${ENTITY_NAME} and its affiliated programs, is intended for educational, ` +
    'informational, and personal development purposes only.',
  'This content is not intended to diagnose, treat, cure, or prevent any medical, psychological, or ' +
    'psychiatric condition. The information provided does not constitute medical advice, mental ' +
    'health counseling, or professional clinical services.',
  'Users are strongly encouraged to consult with a qualified physician, licensed mental health ' +
    'professional, or other appropriate healthcare provider regarding any medical or psychological ' +
    'concerns. Do not disregard or delay seeking professional advice based on information obtained ' +
    'through this platform.',
  `Participation in the ${PRODUCT_NAME} assessment and use of any associated reports or ` +
    'recommendations is voluntary. By engaging with this platform, you acknowledge and agree that:',
];

export const FULL_DISCLAIMER_BULLETS = [
  'You are solely responsible for your health, decisions, and actions.',
  `The ${PRODUCT_NAME} operates as a behavioral and educational framework, not a healthcare provider.`,
  'No guarantees are made regarding outcomes or results.',
  'Individual results may vary based on personal, environmental, and behavioral factors.',
];

export const FULL_DISCLAIMER_CLOSING =
  `To the fullest extent permitted by law, ${ENTITY_NAME} and its affiliates disclaim ` +
  'any liability for any direct, indirect, incidental, or consequential damages arising from the use ' +
  'or misuse of this platform, including but not limited to reliance on assessment results, reports, ' +
  'or recommendations.';

export const CONSENT_CHECKBOXES = [
  {
    id: 'terms',
    required: true,
    label:
      `I agree to the Terms of Use and acknowledge that the ${PRODUCT_NAME} is for educational ` +
      'purposes only and does not provide medical or mental health advice.',
  },
  {
    id: 'responsibility',
    required: true,
    label:
      'I understand that I am responsible for my own decisions and that I should seek a licensed ' +
      'professional for medical or psychological concerns.',
  },
  {
    id: 'research',
    required: false,
    label:
      'I consent to my anonymized data being used for research and system improvement.',
  },
];

export const TERMS_OF_USE = {
  title: `Terms of Use \u2014 ${PRODUCT_NAME}`,
  intro:
    `Welcome to the ${PRODUCT_NAME}, operated by ${ENTITY_NAME}. By accessing or using this ` +
    'platform, you agree to the following Terms of Use.',
  sections: [
    {
      heading: '1. Purpose of the Platform',
      body:
        `The ${PRODUCT_NAME} provides educational, behavioral, and informational content related to ` +
        'executive functioning, decision-making, and personal development. It is not a medical, ' +
        'psychological, or clinical service.',
    },
    {
      heading: '2. No Professional Advice',
      body:
        'All assessments, reports, recommendations, and content are for informational purposes only ' +
        'and do not constitute medical, mental health, legal, or financial advice.',
    },
    {
      heading: '3. User Responsibility',
      body: 'You agree that:',
      bullets: [
        'You are responsible for your own decisions, actions, and outcomes.',
        'You will not rely on this platform as a substitute for professional advice.',
        'You will seek licensed professionals where appropriate.',
      ],
    },
    {
      heading: '4. Assumption of Risk',
      body:
        `Use of this platform is voluntary. You assume full responsibility for any outcomes ` +
        `resulting from your use of the ${PRODUCT_NAME}.`,
    },
    {
      heading: '5. Limitation of Liability',
      body:
        `To the fullest extent permitted by law, ${ENTITY_NAME} and its affiliates shall not be ` +
        'liable for any damages arising from:',
      bullets: [
        'Use or misuse of the platform.',
        'Interpretation of results.',
        'Behavioral, emotional, or decision-making outcomes.',
      ],
    },
    {
      heading: '6. Intellectual Property',
      body:
        'All content, frameworks, visuals, algorithms, and reports are the intellectual property of ' +
        `${ENTITY_NAME} and may not be copied, distributed, or reproduced without permission.`,
    },
    {
      heading: '7. Modifications',
      body:
        'We reserve the right to update these Terms at any time. Continued use constitutes acceptance.',
    },
  ],
};

export const PRIVACY_POLICY = {
  title: `Privacy Policy \u2014 ${PRODUCT_NAME}`,
  intro: 'We respect your privacy and are committed to protecting your information.',
  sections: [
    {
      heading: 'Information Collected',
      bullets: [
        'Assessment responses.',
        'Demographic inputs.',
        'Behavioral patterns (for report generation).',
      ],
    },
    {
      heading: 'How We Use Your Information',
      bullets: [
        'To generate personalized reports.',
        `To improve the ${PRODUCT_NAME} system.`,
        'For research and analytics (anonymized and aggregated).',
      ],
    },
    {
      heading: 'Data Protection',
      body:
        'We implement reasonable safeguards to protect your information. However, no system is ' +
        '100% secure.',
    },
    {
      heading: 'No Sale of Personal Data',
      body: 'We do not sell your personal data.',
    },
    {
      heading: 'User Responsibility',
      body:
        'You agree to provide accurate information and understand how your data is used within the ' +
        'platform.',
    },
  ],
};

export const DATA_USE = {
  title: `Data Use & Research Disclosure \u2014 ${PRODUCT_NAME}`,
  intro:
    `By using the ${PRODUCT_NAME}, you acknowledge that your responses may be used in aggregated, ` +
    'anonymized form for:',
  sections: [
    {
      bullets: [
        'Behavioral research.',
        'System improvement.',
        'Educational and scientific advancement.',
      ],
    },
    {
      body:
        'No personally identifiable information will be shared without explicit consent.',
    },
  ],
};
