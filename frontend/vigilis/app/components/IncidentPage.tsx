"use client";

import React from "react";
import EmbeddedMap from "./map/EmbeddedMapLoader";
import { Incident } from "./Sidebar";

interface IncidentPageProps {
	incident: Incident;
	isPriority?: boolean;
	onTitleClick?: () => void;
}

const IncidentPage: React.FC<IncidentPageProps> = ({
	incident,
	isPriority = false,
	onTitleClick,
}) => {
	const getSeverityColor = (severity: string) => {
		switch (severity) {
			case "high":
				return "bg-d-rl";
			case "medium":
				return "bg-d-s";
			case "low":
				return "bg-d-p";
			default:
				return "bg-d-os2";
		}
	};

	const getSeverityLabel = (severity: string) => {
		switch (severity) {
			case "high":
				return "HIGH SEVERITY";
			case "medium":
				return "MEDIUM SEVERITY";
			case "low":
				return "LOW SEVERITY";
			default:
				return "UNKNOWN";
		}
	};

	return (
		<div className="h-screen flex flex-col px-32 py-16 snap-start">
			<div
				className="flex flex-1 flex-col gap-16 w-full border-2 border-transparent hover:border-d-p transition-colors duration-200 rounded-[32px] p-8 group cursor-pointer"
				onClick={onTitleClick}
			>
				{/* Priority Section */}
				<div className="flex flex-col gap-8 w-full">
					{/* Header */}
					<div className="flex flex-col gap-2.5">
						<div className="flex gap-2.5 items-center">
							<div
								className={`w-2 h-2 rounded-full severity-indicator ${getSeverityColor(
									incident.severity
								)}`}
							/>
							<p className="text-base text-white tracking-[-0.8px]">
								{getSeverityLabel(incident.severity)}
							</p>
						</div>
						<p className="text-[64px] leading-none text-white tracking-[-3.2px] transition-colors group-hover:text-d-p">
							{isPriority ? "PRIORITY: " : ""}
							{incident.title}
						</p>
					</div>

					{/* Live Map Card */}
					<div className="border border-d-os2 rounded-[32px] h-[505px] w-full">
						<div className="flex flex-col gap-2.5 h-[505px] p-8 rounded-inherit">
							<div className="flex gap-2.5 items-center">
								<p className="text-2xl text-white tracking-[-1.2px]">
									Live Map
								</p>
								<svg
									width="24"
									height="24"
									viewBox="0 0 24 24"
									fill="none"
									xmlns="http://www.w3.org/2000/svg"
								>
									<path
										d="M6 6L18 18M18 18V8M18 18H8"
										stroke="white"
										strokeWidth="2"
										strokeLinecap="round"
										strokeLinejoin="round"
									/>
								</svg>
							</div>
							<div className="flex-1 min-h-0 w-full rounded-2xl overflow-hidden">
								<EmbeddedMap />
							</div>
						</div>
					</div>
				</div>

				{/* Bottom Section */}
				<div className="flex flex-1 gap-2.5 w-full min-h-0">
					<div className="flex flex-1 gap-2.5 items-center min-h-0">
						<p className="text-2xl text-white tracking-[-1.2px]">
							Next Suggestions
						</p>
					</div>
					<div className="flex flex-1 flex-col gap-4 h-[113px] justify-center">
						<p className="text-2xl text-white tracking-[-1.2px]">
							Summary
						</p>
						<p className="flex-1 min-h-0 text-xs text-white tracking-[-0.6px] whitespace-pre-wrap">
							Active incident requiring immediate attention. Live
							tracking and monitoring in progress.
						</p>
					</div>
				</div>
			</div>
		</div>
	);
};

export default IncidentPage;
