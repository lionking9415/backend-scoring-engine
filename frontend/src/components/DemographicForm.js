import React, { useState } from 'react';

const SECTIONS = [
  {
    title: 'Age & Developmental Stage',
    fields: [
      {
        key: 'age_range', label: 'What is your age range?', icon: '🎂',
        type: 'single', required: true,
        options: ['13-17', '18-24', '25-34', '35-44', '45-54', '55+'],
      },
    ],
  },
  {
    title: 'Identity (Optional)',
    fields: [
      {
        key: 'gender_identity', label: 'How do you identify?', icon: '👤',
        type: 'single', required: false,
        options: ['Female', 'Male', 'Non-binary', 'Prefer to self-describe', 'Prefer not to say'],
        note: 'Used for research only — will not affect your report.',
      },
      {
        key: 'race_ethnicity', label: 'Race / Ethnicity (select all that apply)', icon: '🌍',
        type: 'multi', required: false,
        options: ['Black / African American', 'Hispanic / Latino', 'White', 'Asian',
          'Native American / Indigenous', 'Middle Eastern / North African',
          'Pacific Islander', 'Other', 'Prefer not to say'],
        note: 'Used for research only — will not affect your report.',
      },
    ],
  },
  {
    title: 'Your Roles & Load',
    fields: [
      {
        key: 'roles', label: 'Which roles currently describe you? (Select all)', icon: '🧑‍💼',
        type: 'multi', required: true,
        options: ['Student', 'Full-time employee', 'Part-time employee',
          'Entrepreneur / Business owner', 'Parent / Caregiver',
          'Unemployed / Between roles', 'Other'],
      },
      {
        key: 'primary_load_sources',
        label: 'What areas place the MOST demand on your daily life? (Up to 3)',
        icon: '⚡', type: 'multi', required: true, maxSelections: 3,
        options: ['School / Academics', 'Work / Career', 'Parenting / Caregiving',
          'Finances', 'Health / Physical well-being', 'Relationships',
          'Major life transition'],
      },
      {
        key: 'perceived_load', label: 'How would you describe your current life load?',
        icon: '📊', type: 'single', required: true,
        options: ['Light', 'Manageable', 'Heavy', 'Overwhelming'],
      },
      {
        key: 'support_level', label: 'How would you describe your current support system?',
        icon: '🤝', type: 'single', required: true,
        options: ['Strong and consistent', 'Available but inconsistent', 'Limited', 'No support'],
      },
    ],
  },
  {
    title: 'Financial Context',
    fields: [
      {
        key: 'financial_stability', label: 'How would you describe your current financial stability?',
        icon: '💰', type: 'single', required: true,
        options: ['Stable', 'Somewhat stable', 'Uncertain', 'High financial stress'],
      },
      {
        key: 'financial_pressure_frequency',
        label: 'How often do financial concerns impact your daily decisions?',
        icon: '💳', type: 'single', required: true,
        options: ['Rarely', 'Sometimes', 'Often', 'Constantly'],
      },
    ],
  },
  {
    title: 'Health & Regulation',
    fields: [
      {
        key: 'health_sleep', label: 'How consistent is your sleep routine?',
        icon: '😴', type: 'single', required: true,
        options: ['Very consistent', 'Somewhat consistent', 'Inconsistent', 'Highly irregular'],
      },
      {
        key: 'health_nutrition', label: 'How would you describe your nutrition habits?',
        icon: '🥗', type: 'single', required: true,
        options: ['Consistent and balanced', 'Somewhat consistent', 'Inconsistent', 'Highly irregular'],
      },
      {
        key: 'health_exercise', label: 'How often do you engage in physical movement or exercise?',
        icon: '🏃', type: 'single', required: true,
        options: ['Regularly', 'Occasionally', 'Rarely', 'Not at all'],
      },
      {
        key: 'health_emotional_regulation',
        label: 'How would you describe your ability to emotionally regulate under stress?',
        icon: '🧘', type: 'single', required: true,
        options: ['Strong and consistent', 'Moderate', 'Inconsistent', 'Difficult'],
      },
    ],
  },
  {
    title: 'Executive Function Context',
    fields: [
      {
        key: 'overwhelm_response',
        label: 'When tasks become overwhelming, what is your most common response?',
        icon: '🧠', type: 'single', required: true,
        options: ['Break tasks into smaller steps', 'Delay or avoid',
          'Jump between tasks', 'Seek help', 'Push through with stress'],
      },
      {
        key: 'planning_style',
        label: 'How do you typically approach planning and organization?',
        icon: '📝', type: 'single', required: true,
        options: ['Structured and consistent', 'Somewhat structured', 'Inconsistent', 'Avoid planning'],
      },
    ],
  },
  {
    title: 'Cultural & Contextual Lens (Optional)',
    fields: [
      {
        key: 'cultural_context',
        label: 'Are there any cultural, community, or personal values that shape how you approach work, school, or daily life?',
        icon: '🌐', type: 'text', required: false,
      },
    ],
  },
];

const DemographicForm = ({ onComplete, onSkip }) => {
  const [formData, setFormData] = useState({});
  const [currentSection, setCurrentSection] = useState(0);

  const handleSingleSelect = (key, value) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const handleMultiSelect = (key, value, maxSelections) => {
    setFormData(prev => {
      const current = prev[key] || [];
      if (current.includes(value)) {
        return { ...prev, [key]: current.filter(v => v !== value) };
      }
      if (maxSelections && current.length >= maxSelections) return prev;
      return { ...prev, [key]: [...current, value] };
    });
  };

  const handleTextChange = (key, value) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const section = SECTIONS[currentSection];
  const isLastSection = currentSection === SECTIONS.length - 1;

  const canProceed = () => {
    return section.fields.every(f => {
      if (!f.required) return true;
      const val = formData[f.key];
      if (f.type === 'multi') return val && val.length > 0;
      return val && val !== '';
    });
  };

  const handleNext = () => {
    if (isLastSection) {
      onComplete({ ...formData, source: 'web_frontend' });
    } else {
      setCurrentSection(prev => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentSection > 0) setCurrentSection(prev => prev - 1);
  };

  const progress = ((currentSection + 1) / SECTIONS.length) * 100;

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-xl w-full">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Progress */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs text-gray-500 font-medium">
                Section {currentSection + 1} of {SECTIONS.length}
              </span>
              <span className="text-xs text-indigo-600 font-semibold">{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-indigo-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Section Title */}
          <h2 className="text-xl font-bold text-indigo-900 mb-1">{section.title}</h2>
          <p className="text-xs text-gray-400 mb-5">
            This helps us personalize your report. Demographics never change your scores.
          </p>

          {/* Fields */}
          <div className="space-y-5">
            {section.fields.map(field => (
              <div key={field.key}>
                <label className="flex items-center text-sm font-semibold text-gray-700 mb-2">
                  <span className="mr-2">{field.icon}</span>
                  {field.label}
                  {field.required && <span className="text-red-400 ml-1">*</span>}
                </label>
                {field.note && (
                  <p className="text-xs text-gray-400 mb-2 ml-6">{field.note}</p>
                )}

                {field.type === 'text' ? (
                  <textarea
                    value={formData[field.key] || ''}
                    onChange={e => handleTextChange(field.key, e.target.value)}
                    placeholder="Share anything that feels relevant (optional)..."
                    className="w-full border-2 border-gray-200 rounded-lg p-3 text-sm focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400 outline-none resize-none"
                    rows={3}
                  />
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {field.options.map(opt => {
                      const isMulti = field.type === 'multi';
                      const selected = isMulti
                        ? (formData[field.key] || []).includes(opt)
                        : formData[field.key] === opt;
                      return (
                        <button
                          key={opt}
                          onClick={() =>
                            isMulti
                              ? handleMultiSelect(field.key, opt, field.maxSelections)
                              : handleSingleSelect(field.key, opt)
                          }
                          className={`px-3 py-2 rounded-lg text-sm font-medium border-2 transition-all ${
                            selected
                              ? 'bg-indigo-600 text-white border-indigo-600 shadow-md'
                              : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300 hover:bg-indigo-50'
                          }`}
                        >
                          {opt}
                        </button>
                      );
                    })}
                  </div>
                )}
                {field.maxSelections && (
                  <p className="text-xs text-gray-400 mt-1 ml-1">
                    {(formData[field.key] || []).length}/{field.maxSelections} selected
                  </p>
                )}
              </div>
            ))}
          </div>

          {/* Navigation */}
          <div className="mt-8 flex gap-3">
            {currentSection > 0 && (
              <button
                onClick={handleBack}
                className="px-6 py-3 rounded-xl text-sm font-semibold text-gray-600 border-2 border-gray-200 hover:bg-gray-50 transition-all"
              >
                Back
              </button>
            )}
            <button
              onClick={handleNext}
              disabled={!canProceed()}
              className={`flex-1 py-3 px-6 rounded-xl text-sm font-bold transition-all ${
                canProceed()
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              {isLastSection ? 'Continue to Assessment' : 'Next Section'} →
            </button>
          </div>

          {/* Skip */}
          <button
            onClick={() => onSkip()}
            className="w-full text-gray-400 hover:text-gray-600 text-xs py-3 mt-2 transition-colors"
          >
            Skip intake — proceed directly to assessment
          </button>
        </div>
      </div>
    </div>
  );
};

export default DemographicForm;
