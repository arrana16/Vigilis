'use client';

import dynamic from 'next/dynamic';

// Dynamically import the Map component with no SSR
const Map = dynamic(() => import('./Map'), {
	ssr: false,
	loading: () => (
		<div className="w-full h-screen flex items-center justify-center bg-black">
			<div className="text-white text-xl">Loading map...</div>
		</div>
	),
});

export default Map;
