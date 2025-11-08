'use client';

import { useState, useEffect, useRef } from 'react';
import Sidebar, { incidents } from './components/Sidebar';
import IncidentPage from './components/IncidentPage';
import DetailPage from './components/DetailPage';

export default function Home() {
	const [activeIncidentId, setActiveIncidentId] = useState<string>(
		incidents[0]?.id || ''
	);
	const [showDetail, setShowDetail] = useState(false);
	const scrollContainerRef = useRef<HTMLDivElement>(null);

	useEffect(() => {
		if (showDetail) return; // Don't observe when in detail view

		const scrollContainer = scrollContainerRef.current;
		if (!scrollContainer) return;

		const observer = new IntersectionObserver(
			(entries) => {
				entries.forEach((entry) => {
					if (entry.isIntersecting && entry.intersectionRatio >= 0.5) {
						const incidentId = entry.target.getAttribute(
							'data-incident-id'
						);
						if (incidentId) {
							setActiveIncidentId(incidentId);
						}
					}
				});
			},
			{
				root: scrollContainer,
				threshold: [0.5],
			}
		);

		const pages = scrollContainer.querySelectorAll('[data-incident-id]');
		pages.forEach((page) => observer.observe(page));

		return () => observer.disconnect();
	}, [showDetail]);

	const handleIncidentClick = (incidentId: string) => {
		setActiveIncidentId(incidentId);
		setShowDetail(true);
	};

	const handleBackClick = () => {
		setShowDetail(false);
	};

	const activeIncident = incidents.find((inc) => inc.id === activeIncidentId) || incidents[0];

	if (showDetail) {
		return <DetailPage incident={activeIncident} onBack={handleBackClick} />;
	}

	return (
		<div className="bg-d-bg flex gap-2.5 items-start p-4 h-screen overflow-hidden animate-fadeIn">
			{/* Sidebar */}
			<Sidebar activeIncidentId={activeIncidentId} />

			{/* Main Content - Snap Scroll Container */}
			<div
				ref={scrollContainerRef}
				className="flex-1 h-screen overflow-y-scroll snap-y snap-mandatory"
				style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
			>
				{incidents.map((incident, index) => (
					<div key={incident.id} data-incident-id={incident.id}>
						<IncidentPage
							incident={incident}
							isPriority={index === 0}
							onTitleClick={() => handleIncidentClick(incident.id)}
						/>
					</div>
				))}
			</div>

			<style jsx>{`
				div::-webkit-scrollbar {
					display: none;
				}
			`}</style>
		</div>
	);
}
