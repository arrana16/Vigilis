"use client";

import dynamic from "next/dynamic";
import { useEffect } from "react";
import type { PoliceOfficer } from "./EmbeddedMap";

// Props interface
interface EmbeddedMapWrapperProps {
	incidentLocation?: [number, number]; // [lng, lat] - if provided, shows incident view
	policeOfficers?: PoliceOfficer[]; // array of police officer positions
	onOfficerClick?: (officer: PoliceOfficer) => void; // callback when officer marker is clicked
	hoveredOfficerId?: string | null; // ID of officer being hovered in dispatch UI
	selectedOfficerId?: string | null; // ID of officer whose route should be shown
}

const EmbeddedMap = dynamic(() => import("./EmbeddedMap"), {
	ssr: false,
	loading: () => {
		console.log("[EmbeddedMapLoader] Showing loading state...");
		return (
			<div className="w-full h-full flex items-center justify-center bg-d-bg rounded-2xl">
				<div className="text-white text-sm">Loading map...</div>
			</div>
		);
	},
});

const EmbeddedMapWrapper: React.FC<EmbeddedMapWrapperProps> = ({
	incidentLocation,
	policeOfficers,
	onOfficerClick,
	hoveredOfficerId,
	selectedOfficerId,
}) => {
	useEffect(() => {
		console.log(
			"[EmbeddedMapLoader] Component mounted with incidentLocation:",
			incidentLocation,
			"officers:",
			policeOfficers?.length
		);
	}, [incidentLocation, policeOfficers]);

	return (
		<EmbeddedMap
			incidentLocation={incidentLocation}
			policeOfficers={policeOfficers}
			onOfficerClick={onOfficerClick}
			hoveredOfficerId={hoveredOfficerId}
			selectedOfficerId={selectedOfficerId}
		/>
	);
};

export default EmbeddedMapWrapper;
