import React, { useState } from 'react';

const DemographicForm = ({ onComplete, onSkip }) => {
  const [formData, setFormData] = useState({
    age_range: '',
    gender: '',
    education: '',
    referral_source: '',
  });

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = () => {
    // Filter out empty fields
    const demographics = { source: 'web_frontend' };
    if (formData.age_range) demographics.age_range = formData.age_range;
    if (formData.gender) demographics.gender = formData.gender;
    if (formData.education) demographics.education = formData.education;
    if (formData.referral_source) demographics.referral_source = formData.referral_source;
    onComplete(demographics);
  };

  const fields = [
    {
      key: 'age_range',
      label: 'Age Range',
      icon: '🎂',
      options: ['Under 18', '18–24', '25–34', '35–44', '45–54', '55–64', '65+'],
    },
    {
      key: 'gender',
      label: 'Gender',
      icon: '👤',
      options: ['Female', 'Male', 'Non-binary', 'Prefer not to say'],
    },
    {
      key: 'education',
      label: 'Education Level',
      icon: '🎓',
      options: ['High School', 'Some College', "Bachelor's Degree", "Master's Degree", 'Doctorate', 'Other'],
    },
    {
      key: 'referral_source',
      label: 'How did you hear about us?',
      icon: '📣',
      options: ['Social Media', 'Friend / Family', 'School / University', 'Employer', 'Web Search', 'Other'],
    },
  ];

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-lg w-full">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-6">
            <span className="text-4xl mb-3 block">📋</span>
            <h2 className="text-2xl font-bold text-indigo-900 mb-2">
              Quick Background Info
            </h2>
            <p className="text-gray-500 text-sm">
              This helps us tailor insights and supports our research.
              <br />All fields are optional.
            </p>
          </div>

          <div className="space-y-5">
            {fields.map(field => (
              <div key={field.key}>
                <label className="flex items-center text-sm font-semibold text-gray-700 mb-2">
                  <span className="mr-2">{field.icon}</span>
                  {field.label}
                </label>
                <div className="flex flex-wrap gap-2">
                  {field.options.map(opt => (
                    <button
                      key={opt}
                      onClick={() => handleChange(field.key, opt)}
                      className={`px-3 py-2 rounded-lg text-sm font-medium border-2 transition-all ${
                        formData[field.key] === opt
                          ? 'bg-indigo-600 text-white border-indigo-600 shadow-md'
                          : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300 hover:bg-indigo-50'
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-8 flex flex-col space-y-3">
            <button
              onClick={handleSubmit}
              className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold py-4 px-6 rounded-xl text-lg shadow-lg hover:shadow-xl transition-all"
            >
              Continue to Assessment →
            </button>
            <button
              onClick={() => onSkip()}
              className="w-full text-gray-400 hover:text-gray-600 text-sm py-2 transition-colors"
            >
              Skip — I'd rather not share
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DemographicForm;
