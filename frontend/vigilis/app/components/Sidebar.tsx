'use client';

import React from 'react';

export interface Incident {
	id: string;
	severity: 'high' | 'medium' | 'low';
	title: string;
	lastUpdated: string;
}

export const incidents: Incident[] = [
	{
		id: '1',
		severity: 'high',
		title: 'Police Chase',
		lastUpdated: '8:46 PM',
	},
	{
		id: '2',
		severity: 'medium',
		title: 'Cardiac Arrest',
		lastUpdated: '8:46 PM',
	},
];

interface SidebarProps {
	activeIncidentId?: string;
}

const Sidebar: React.FC<SidebarProps> = ({ activeIncidentId }) => {
	const getSeverityColor = (severity: string) => {
		switch (severity) {
			case 'high':
				return 'bg-d-rl';
			case 'medium':
				return 'bg-d-s';
			case 'low':
				return 'bg-d-p';
			default:
				return 'bg-d-os2';
		}
	};

	const getSeverityLabel = (severity: string) => {
		switch (severity) {
			case 'high':
				return 'HIGH SEVERITY';
			case 'medium':
				return 'MEDIUM SEVERITY';
			case 'low':
				return 'LOW SEVERITY';
			default:
				return 'UNKNOWN';
		}
	};

	return (
		<div className="h-[calc(100vh-2rem)] w-64 border border-d-os2 rounded-2xl sticky top-4">
			<div className="flex flex-col gap-8 h-full overflow-clip p-4 rounded-inherit">
				{/* Branding */}
				<div className="flex flex-col gap-2">
					<p className="text-[64px] leading-none text-white tracking-[-3.2px]">
						Vigilis
					</p>
					<div className="h-0 w-[220px] relative">
						<div className="absolute bottom-0 left-0 right-0 top-[-1px]">
							<svg
								width="220"
								height="1"
								viewBox="0 0 220 1"
								fill="none"
								xmlns="http://www.w3.org/2000/svg"
							>
								<line
									x1="0"
									y1="0.5"
									x2="220"
									y2="0.5"
									stroke="#A4CAED"
									strokeWidth="1"
								/>
							</svg>
						</div>
					</div>
				</div>

				{/* Ongoing Incidents */}
				<div className="flex flex-col gap-4 w-full">
					<p className="text-base text-white tracking-[-0.8px]">
						Ongoing Incidents
					</p>
					<div className="flex flex-col gap-4">
						{incidents.map((incident) => {
							const isActive = activeIncidentId === incident.id;
							return (
								<div
									key={incident.id}
									className={`flex flex-col gap-8 overflow-clip p-4 rounded-2xl transition-all duration-300 ${
										isActive
											? 'bg-d-os text-d-bg'
											: 'bg-[#1a1a1a]'
									}`}
								>
									<div className="flex flex-col gap-2">
										<div className="flex gap-2.5 items-center">
											<div
												className={`w-2 h-2 rounded-full severity-indicator ${getSeverityColor(
													incident.severity
												)}`}
											/>
											<p
												className={`text-xs font-semibold tracking-[-0.6px] ${
													isActive
														? 'text-d-bg'
														: 'text-white'
												}`}
											>
												{getSeverityLabel(incident.severity)}
											</p>
										</div>
										<p
											className={`text-2xl tracking-[-1.2px] whitespace-pre-wrap ${
												isActive ? 'text-d-bg' : 'text-white'
											}`}
										>
											{incident.title}
										</p>
									</div>
									<p
										className={`text-xs tracking-[-0.6px] ${
											isActive
												? 'text-d-bg/50'
												: 'text-white/50'
										}`}
									>
										Last Updated: {incident.lastUpdated}
									</p>
								</div>
							);
						})}
					</div>
				</div>
			</div>
		</div>
	);
};

export default Sidebar;
