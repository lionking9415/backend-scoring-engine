import React from 'react';

const LockedSections = ({ features }) => {
  if (!features || features.length === 0) return null;

  return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-800 mb-5">
        Your Full Galaxy Report Awaits
      </h2>

      <div className="space-y-3">
        {features.map((feat, idx) => (
          <div
            key={idx}
            className="relative overflow-hidden rounded-xl border border-gray-200 p-4"
          >
            {/* Blur overlay */}
            <div className="absolute inset-0 backdrop-blur-[2px] bg-white/60 z-10 flex items-center justify-center">
              <div className="text-center px-4">
                <span className="text-2xl block mb-1">🔒</span>
                <p className="text-gray-700 text-sm font-medium">{feat.message}</p>
              </div>
            </div>

            {/* Faux content behind blur */}
            <div className="opacity-30 select-none" aria-hidden="true">
              <h3 className="font-bold text-gray-800 mb-2">{feat.name}</h3>
              <div className="space-y-1">
                <div className="h-3 bg-gray-300 rounded w-full"></div>
                <div className="h-3 bg-gray-300 rounded w-5/6"></div>
                <div className="h-3 bg-gray-300 rounded w-4/6"></div>
                <div className="h-3 bg-gray-200 rounded w-3/6"></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Upgrade CTA */}
      <div className="mt-6 text-center">
        <p className="text-gray-500 text-sm mb-4">
          Unlock your full Galaxy Report to see how everything connects.
        </p>
        <button className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold py-3 px-8 rounded-xl text-lg shadow-lg hover:shadow-xl transition-all duration-200">
          Unlock Full Galaxy Report
        </button>
        <p className="text-gray-400 text-xs mt-2">Coming soon</p>
      </div>
    </div>
  );
};

export default LockedSections;
