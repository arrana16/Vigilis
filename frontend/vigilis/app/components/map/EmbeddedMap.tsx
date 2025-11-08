"use client";

import React, { useRef, useEffect } from "react";
import mapboxgl from "mapbox-gl";
import * as turf from "@turf/turf";
import "mapbox-gl/dist/mapbox-gl.css";

// Police officer data structure
export interface PoliceOfficer {
	id: string;
	name: string;
	role: string;
	location: [number, number]; // [lng, lat]
	heading?: number; // direction in degrees (0-360)
	speed?: number; // meters per second
	badge?: string; // badge number
	unit?: string; // unit/car number
	rank?: string; // officer rank
	yearsOfService?: number;
	dispatched?: boolean; // whether officer is dispatched to incident
}

// Component props
interface EmbeddedMapProps {
	incidentLocation?: [number, number]; // [lng, lat] - if provided, shows incident view
	policeOfficers?: PoliceOfficer[]; // array of police officer positions
	onOfficerClick?: (officer: PoliceOfficer) => void; // callback when officer marker is clicked
	hoveredOfficerId?: string | null; // ID of officer being hovered in dispatch UI
	selectedOfficerId?: string | null; // ID of officer whose route should be shown
}

// Route info interface for calculating ETA
export interface RouteInfo {
	distance: number; // in meters
	duration: number; // in seconds
	geometry: [number, number][]; // route coordinates
}

// Stadium coordinates
const BOBBY_DODD = [-84.3933, 33.7726];
const MERCEDES_BENZ = [-84.4008, 33.7552];

// Easing function for smooth ease-in-ease-out
function easeInOutCubic(t: number): number {
	return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

// Helper function to fetch route information from Mapbox Directions API
export async function fetchRouteToIncident(
	officerLocation: [number, number],
	incidentLocation: [number, number]
): Promise<RouteInfo | null> {
	const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
	if (!token) {
		console.error("Mapbox token not found");
		return null;
	}

	const url = `https://api.mapbox.com/directions/v5/mapbox/driving/${officerLocation[0]},${officerLocation[1]};${incidentLocation[0]},${incidentLocation[1]}?geometries=geojson&access_token=${token}`;

	try {
		const response = await fetch(url);
		const data = await response.json();

		if (data.routes && data.routes.length > 0) {
			const route = data.routes[0];
			return {
				distance: route.distance, // in meters
				duration: route.duration, // in seconds
				geometry: route.geometry.coordinates,
			};
		}
	} catch (error) {
		console.error("Error fetching route:", error);
	}

	return null;
}

// Function to add route to map with cinematic animation
async function addRouteToMap(map: mapboxgl.Map) {
	console.log("[addRouteToMap] Starting route addition");
	const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

	if (!token) {
		console.error("[addRouteToMap] Mapbox token not found");
		return;
	}

	try {
		const url = `https://api.mapbox.com/directions/v5/mapbox/driving/${BOBBY_DODD[0]},${BOBBY_DODD[1]};${MERCEDES_BENZ[0]},${MERCEDES_BENZ[1]}?steps=true&geometries=geojson&access_token=${token}`;
		console.log("[addRouteToMap] Fetching route from Mapbox API");

		const response = await fetch(url);
		const data = await response.json();
		console.log("[addRouteToMap] Route data received:", data);

		if (!data.routes || data.routes.length === 0) {
			console.error("[addRouteToMap] No route found in response");
			return;
		}

		console.log("[addRouteToMap] Route found, adding to map");

		const route = data.routes[0];
		const routeCoordinates = route.geometry.coordinates;
		const routeLine = turf.lineString(routeCoordinates);
		const routeDistance = turf.length(routeLine, { units: "kilometers" });

		map.addSource("route", {
			type: "geojson",
			lineMetrics: true,
			data: {
				type: "Feature",
				properties: {},
				geometry: {
					type: "LineString",
					coordinates: routeCoordinates,
				},
			},
		});

		map.addLayer({
			id: "route-line",
			type: "line",
			source: "route",
			layout: {
				"line-join": "round",
				"line-cap": "round",
			},
			paint: {
				"line-color": "#ff0000",
				"line-width": 4,
				"line-gradient": [
					"step",
					["line-progress"],
					"#ff0000",
					0,
					"rgba(255, 0, 0, 0)",
				],
			},
		});

		map.addLayer({
			id: "route-glow",
			type: "line",
			source: "route",
			layout: {
				"line-join": "round",
				"line-cap": "round",
			},
			paint: {
				"line-color": "#ff0000",
				"line-width": 10,
				"line-blur": 4,
				"line-gradient": [
					"step",
					["line-progress"],
					"rgba(255, 0, 0, 0.4)",
					0,
					"rgba(255, 0, 0, 0)",
				],
			},
		});

		const animationDuration = 5000;
		const startTime = Date.now();
		let cameraPosition: [number, number] | null = null;
		const lerpFactor = 0.4;

		function animateRoute() {
			const elapsed = Date.now() - startTime;
			const linearProgress = Math.min(elapsed / animationDuration, 1);
			const progress = easeInOutCubic(linearProgress);

			map.setPaintProperty("route-line", "line-gradient", [
				"step",
				["line-progress"],
				"#ff0000",
				progress,
				"rgba(255, 0, 0, 0)",
			]);

			map.setPaintProperty("route-glow", "line-gradient", [
				"step",
				["line-progress"],
				"rgba(255, 0, 0, 0.4)",
				progress,
				"rgba(255, 0, 0, 0)",
			]);

			const distanceAlongRoute = progress * routeDistance;
			const currentPoint = turf.along(routeLine, distanceAlongRoute, {
				units: "kilometers",
			});
			const currentCoords = currentPoint.geometry.coordinates as [
				number,
				number
			];

			const targetPosition = currentCoords;

			if (!cameraPosition) {
				cameraPosition = targetPosition;
			} else {
				cameraPosition = [
					cameraPosition[0] +
						(targetPosition[0] - cameraPosition[0]) * lerpFactor,
					cameraPosition[1] +
						(targetPosition[1] - cameraPosition[1]) * lerpFactor,
				];
			}

			map.easeTo({
				center: cameraPosition,
				zoom: 15,
				duration: 0,
				pitch: 50,
				bearing: progress * 30,
			});

			if (linearProgress < 1) {
				requestAnimationFrame(animateRoute);
			}
		}

		console.log("[addRouteToMap] Starting route animation");
		setTimeout(() => {
			requestAnimationFrame(animateRoute);
		}, 500);
	} catch (error) {
		console.error("[addRouteToMap] Error fetching route:", error);
	}
}

// Function to add flashing incident marker
function addIncidentMarker(map: mapboxgl.Map, location: [number, number]) {
	console.log("[addIncidentMarker] Adding incident marker at:", location);

	// Create a circle feature at the incident location
	// We'll use a fill-extrusion layer to make it appear on the ground with proper perspective
	map.addSource("incident-circle", {
		type: "geojson",
		data: {
			type: "Feature",
			properties: {},
			geometry: {
				type: "Point",
				coordinates: location,
			},
		},
	});

	// Add a pulsing circle layer that sits on the ground
	map.addLayer({
		id: "incident-pulse-outer",
		type: "circle",
		source: "incident-circle",
		paint: {
			"circle-radius": [
				"interpolate",
				["linear"],
				["zoom"],
				10,
				5,
				15,
				25,
				20,
				80,
			],
			"circle-color": "#da3c3c",
			"circle-opacity": 0.3,
			"circle-blur": 0.5,
		},
	});

	map.addLayer({
		id: "incident-pulse-middle",
		type: "circle",
		source: "incident-circle",
		paint: {
			"circle-radius": [
				"interpolate",
				["linear"],
				["zoom"],
				10,
				3,
				15,
				15,
				20,
				50,
			],
			"circle-color": "#f48484",
			"circle-opacity": 0.5,
		},
	});

	map.addLayer({
		id: "incident-pulse-inner",
		type: "circle",
		source: "incident-circle",
		paint: {
			"circle-radius": [
				"interpolate",
				["linear"],
				["zoom"],
				10,
				2,
				15,
				8,
				20,
				25,
			],
			"circle-color": "#da3c3c",
			"circle-opacity": 1,
			"circle-stroke-width": 2,
			"circle-stroke-color": "#ffffff",
		},
	});

	// Animate the outer circle with a pulsing effect
	let radiusScale = 1;
	let growing = true;

	function animatePulse() {
		if (growing) {
			radiusScale += 0.02;
			if (radiusScale >= 1.5) growing = false;
		} else {
			radiusScale -= 0.02;
			if (radiusScale <= 1) growing = true;
		}

		const opacity = (0.3 * (1.5 - radiusScale)) / 0.5;

		map.setPaintProperty("incident-pulse-outer", "circle-radius", [
			"interpolate",
			["linear"],
			["zoom"],
			10,
			5 * radiusScale,
			15,
			25 * radiusScale,
			20,
			80 * radiusScale,
		]);

		map.setPaintProperty("incident-pulse-outer", "circle-opacity", opacity);

		requestAnimationFrame(animatePulse);
	}

	animatePulse();

	console.log("[addIncidentMarker] Incident marker added successfully");
}

// Function to add police officer markers with movement
function addPoliceOfficers(
	map: mapboxgl.Map,
	officers: PoliceOfficer[],
	onOfficerClick?: (officer: PoliceOfficer) => void,
	getLatestOfficers?: () => PoliceOfficer[] // Function to get latest officer data
) {
	console.log("[addPoliceOfficers] Adding officers:", officers);

	// Store officer positions and routes for animation
	const officerData = new Map<
		string,
		{
			current: [number, number];
			route: [number, number][];
			routeIndex: number;
			heading: number;
			waitingUntil: number | null; // Timestamp when waiting ends
			segmentProgress: number; // 0-1 progress through current segment
			segmentStartTime: number; // When we started moving to current waypoint
		}
	>();

	// Initialize each officer with their starting position
	officers.forEach((officer) => {
		const heading = officer.heading || Math.random() * 360;
		officerData.set(officer.id, {
			current: officer.location,
			route: [],
			routeIndex: 0,
			heading: heading,
			waitingUntil: null,
			segmentProgress: 0,
			segmentStartTime: Date.now(),
		});

		// Fetch a route for each officer to patrol
		fetchPatrolRoute(officer.location).then((route) => {
			const data = officerData.get(officer.id);
			if (data && route) {
				data.route = route;
				data.routeIndex = 0;
			}
		});
	});

	// Fetch a patrol route using Mapbox Directions API
	async function fetchPatrolRoute(
		start: [number, number]
	): Promise<[number, number][] | null> {
		const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
		if (!token) return null;

		try {
			// Create a random patrol route within ~200 meters
			const distance = 0.002; // approximately 200 meters
			const angle1 = Math.random() * Math.PI * 2;
			const angle2 =
				angle1 + Math.PI / 2 + (Math.random() - 0.5) * Math.PI;

			const waypoint1: [number, number] = [
				start[0] + Math.cos(angle1) * distance,
				start[1] + Math.sin(angle1) * distance,
			];

			const waypoint2: [number, number] = [
				start[0] + Math.cos(angle2) * distance,
				start[1] + Math.sin(angle2) * distance,
			];

			// Get route that follows roads
			const url = `https://api.mapbox.com/directions/v5/mapbox/driving/${start[0]},${start[1]};${waypoint1[0]},${waypoint1[1]};${waypoint2[0]},${waypoint2[1]};${start[0]},${start[1]}?geometries=geojson&access_token=${token}`;

			const response = await fetch(url);
			const data = await response.json();

			if (data.routes && data.routes[0]) {
				return data.routes[0].geometry.coordinates as [
					number,
					number
				][];
			}
		} catch (error) {
			console.error("[fetchPatrolRoute] Error:", error);
		}

		return null;
	}

	// Add source for police officers
	const officersGeoJSON: GeoJSON.FeatureCollection = {
		type: "FeatureCollection",
		features: officers.map((officer) => ({
			type: "Feature",
			properties: {
				id: officer.id,
				name: officer.name,
				role: officer.role,
				heading: officer.heading || 0,
			},
			geometry: {
				type: "Point",
				coordinates: officer.location,
			},
		})),
	};

	map.addSource("police-officers", {
		type: "geojson",
		data: officersGeoJSON,
	});

	// Add a blue pulsing circle for each officer
	map.addLayer({
		id: "officer-pulse",
		type: "circle",
		source: "police-officers",
		paint: {
			"circle-radius": [
				"interpolate",
				["linear"],
				["zoom"],
				10,
				3,
				15,
				12,
				20,
				40,
			],
			"circle-color": [
				"case",
				["get", "dispatched"],
				"#9333ea", // Purple for dispatched officers
				"#3c56da", // Blue for available officers
			],
			"circle-opacity": 0.3,
			"circle-blur": 0.5,
		},
	});

	// Add main officer marker
	map.addLayer({
		id: "officer-marker",
		type: "circle",
		source: "police-officers",
		paint: {
			"circle-radius": [
				"interpolate",
				["linear"],
				["zoom"],
				10,
				2,
				15,
				6,
				20,
				20,
			],
			"circle-color": [
				"case",
				["get", "dispatched"],
				"#9333ea", // Purple for dispatched officers
				"#3c56da", // Blue for available officers
			],
			"circle-opacity": 1,
			"circle-stroke-width": 2,
			"circle-stroke-color": [
				"case",
				["get", "dispatched"],
				"#c084fc", // Lighter purple stroke for dispatched
				"#a4caed", // Light blue stroke for available
			],
		},
	});

	// Add highlight layer for hovered officer
	map.addLayer({
		id: "officer-highlight",
		type: "circle",
		source: "police-officers",
		paint: {
			"circle-radius": [
				"interpolate",
				["linear"],
				["zoom"],
				10,
				4,
				15,
				12,
				20,
				40,
			],
			"circle-color": "#a4caed",
			"circle-opacity": 0.5,
			"circle-stroke-width": 3,
			"circle-stroke-color": "#ffffff",
		},
		filter: ["==", ["get", "id"], ""], // Initially show nothing
	});

	// Add label with officer name
	map.addLayer({
		id: "officer-label",
		type: "symbol",
		source: "police-officers",
		layout: {
			"text-field": ["get", "name"],
			"text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
			"text-size": 11,
			"text-offset": [0, 1.5],
			"text-anchor": "top",
		},
		paint: {
			"text-color": "#a4caed",
			"text-halo-color": "#101010",
			"text-halo-width": 1,
		},
	});

	// Make officers clickable
	map.on("click", "officer-marker", (e) => {
		if (e.features && e.features[0] && onOfficerClick) {
			const feature = e.features[0];
			const officerId = feature.properties?.id;
			const officer = officers.find((o) => o.id === officerId);
			if (officer) {
				console.log("[addPoliceOfficers] Officer clicked:", officer);
				onOfficerClick(officer);
			}
		}
	});

	// Change cursor on hover
	map.on("mouseenter", "officer-marker", () => {
		map.getCanvas().style.cursor = "pointer";
	});

	map.on("mouseleave", "officer-marker", () => {
		map.getCanvas().style.cursor = "";
	});

	// Animate officer movement along routes
	function animateOfficers() {
		const now = Date.now();

		// Get the latest officer data (including updated dispatched status)
		const currentOfficers = getLatestOfficers
			? getLatestOfficers()
			: officers;

		const features = currentOfficers
			.map((officer) => {
				const data = officerData.get(officer.id);
				if (!data || data.route.length === 0) {
					// No route yet, stay at current position
					return {
						type: "Feature" as const,
						properties: {
							id: officer.id,
							name: officer.name,
							role: officer.role,
							heading: data?.heading || 0,
							dispatched: officer.dispatched || false,
						},
						geometry: {
							type: "Point" as const,
							coordinates: data?.current || officer.location,
						},
					};
				}

				// Check if officer is waiting at an intersection
				if (data.waitingUntil !== null) {
					if (now < data.waitingUntil) {
						// Still waiting, don't move
						return {
							type: "Feature" as const,
							properties: {
								id: officer.id,
								name: officer.name,
								role: officer.role,
								heading: data.heading,
								dispatched: officer.dispatched || false,
							},
							geometry: {
								type: "Point" as const,
								coordinates: data.current,
							},
						};
					} else {
						// Done waiting, clear the wait state and reset segment progress
						data.waitingUntil = null;
						data.segmentProgress = 0;
						data.segmentStartTime = now;
					}
				}

				// Move along the route
				const targetPoint = data.route[data.routeIndex];
				const dx = targetPoint[0] - data.current[0];
				const dy = targetPoint[1] - data.current[1];
				const distance = Math.sqrt(dx * dx + dy * dy);

				if (distance > 0.000005) {
					// Still moving towards current waypoint with easing
					const baseSpeed = 0.0000015; // Base speed (reduced from 0.000002 for slower movement)

					// Calculate progress through this segment (0 to 1)
					const elapsed = now - data.segmentStartTime;
					const estimatedDuration = 15000; // Estimated time to reach waypoint (15 seconds)
					data.segmentProgress = Math.min(
						elapsed / estimatedDuration,
						1
					);

					// Apply ease-in-out easing to the speed
					const easedProgress = easeInOutCubic(data.segmentProgress);

					// Speed multiplier: slow at start/end, fast in middle
					const speedMultiplier =
						1 + Math.sin(easedProgress * Math.PI) * 2;
					const adjustedSpeed = baseSpeed * speedMultiplier;

					const ratio = Math.min(adjustedSpeed / distance, 1);
					data.current = [
						data.current[0] + dx * ratio,
						data.current[1] + dy * ratio,
					];
					data.heading = (Math.atan2(dy, dx) * 180) / Math.PI;
				} else {
					// Reached waypoint (intersection), start waiting
					data.waitingUntil = now + 2000 + Math.random() * 1000; // Wait 2-3 seconds
					data.routeIndex++;
					if (data.routeIndex >= data.route.length) {
						// Completed the route, loop back to start
						data.routeIndex = 0;
					}
				}

				return {
					type: "Feature" as const,
					properties: {
						id: officer.id,
						name: officer.name,
						role: officer.role,
						heading: data.heading,
						dispatched: officer.dispatched || false,
					},
					geometry: {
						type: "Point" as const,
						coordinates: data.current,
					},
				};
			})
			.filter((f) => f !== null);

		const source = map.getSource(
			"police-officers"
		) as mapboxgl.GeoJSONSource;
		if (source) {
			source.setData({
				type: "FeatureCollection",
				features: features as GeoJSON.Feature[],
			});
		}

		requestAnimationFrame(animateOfficers);
	}

	animateOfficers();

	console.log("[addPoliceOfficers] Officers added successfully");
}

const EmbeddedMap: React.FC<EmbeddedMapProps> = ({
	incidentLocation,
	policeOfficers,
	onOfficerClick,
	hoveredOfficerId,
	selectedOfficerId,
}) => {
	const mapContainer = useRef<HTMLDivElement>(null);
	const map = useRef<mapboxgl.Map | null>(null);
	const initialized = useRef(false);
	// Store latest policeOfficers for animation loop
	const policeOfficersRef = useRef<PoliceOfficer[]>(policeOfficers || []);

	// Update the ref whenever policeOfficers prop changes
	useEffect(() => {
		policeOfficersRef.current = policeOfficers || [];
	}, [policeOfficers]);

	// Update highlight when hoveredOfficerId changes
	useEffect(() => {
		if (!map.current) return;

		// Update the filter to highlight the hovered officer
		if (hoveredOfficerId) {
			map.current.setFilter("officer-highlight", [
				"==",
				["get", "id"],
				hoveredOfficerId,
			]);
		} else {
			map.current.setFilter("officer-highlight", [
				"==",
				["get", "id"],
				"",
			]);
		}
	}, [hoveredOfficerId]);

	// Draw route to incident when officer is selected
	useEffect(() => {
		if (!map.current || !incidentLocation || !selectedOfficerId) {
			// Remove route layer if it exists
			if (map.current && map.current.getLayer("selected-officer-route")) {
				map.current.removeLayer("selected-officer-route");
			}
			if (
				map.current &&
				map.current.getSource("selected-officer-route")
			) {
				map.current.removeSource("selected-officer-route");
			}
			return;
		}

		const selectedOfficer = policeOfficers?.find(
			(o) => o.id === selectedOfficerId
		);
		if (!selectedOfficer) return;

		// Fetch route from officer to incident
		const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
		if (!token) return;

		const start = selectedOfficer.location;
		const end = incidentLocation;
		const url = `https://api.mapbox.com/directions/v5/mapbox/driving/${start[0]},${start[1]};${end[0]},${end[1]}?geometries=geojson&access_token=${token}`;

		fetch(url)
			.then((response) => response.json())
			.then((data) => {
				if (data.routes && data.routes.length > 0) {
					const route = data.routes[0];
					const coordinates = route.geometry.coordinates;

					// Remove existing route if any
					if (map.current!.getLayer("selected-officer-route")) {
						map.current!.removeLayer("selected-officer-route");
					}
					if (map.current!.getSource("selected-officer-route")) {
						map.current!.removeSource("selected-officer-route");
					}

					// Add route source
					map.current!.addSource("selected-officer-route", {
						type: "geojson",
						data: {
							type: "Feature",
							properties: {},
							geometry: {
								type: "LineString",
								coordinates: coordinates,
							},
						},
					});

					// Add route layer with purple color for dispatched route
					map.current!.addLayer({
						id: "selected-officer-route",
						type: "line",
						source: "selected-officer-route",
						layout: {
							"line-join": "round",
							"line-cap": "round",
						},
						paint: {
							"line-color": "#9333ea",
							"line-width": 4,
							"line-opacity": 0.8,
						},
					});
				}
			})
			.catch((error) => {
				console.error("Error fetching route:", error);
			});
	}, [selectedOfficerId, incidentLocation, policeOfficers]);

	// Update route dynamically as officer moves
	useEffect(() => {
		if (!map.current || !incidentLocation || !selectedOfficerId) {
			return;
		}

		let animationFrameId: number;
		let lastUpdateTime = 0;
		const updateInterval = 3000; // Update route every 3 seconds

		const updateRoute = async (currentTime: number) => {
			if (currentTime - lastUpdateTime >= updateInterval) {
				lastUpdateTime = currentTime;

				const selectedOfficer = policeOfficers?.find(
					(o) => o.id === selectedOfficerId
				);
				if (!selectedOfficer) return;

				// Get the officer's current position from the map source
				const source = map.current!.getSource(
					"police-officers"
				) as mapboxgl.GeoJSONSource;
				if (
					source &&
					(source as unknown as { _data: GeoJSON.FeatureCollection })
						._data
				) {
					// Fetch new route from current position to incident
					const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
					if (!token) return;

					// Get current officer position from the GeoJSON data
					const data = (
						source as unknown as {
							_data: GeoJSON.FeatureCollection;
						}
					)._data;
					const officerFeature = data.features.find(
						(f: GeoJSON.Feature) => {
							const props = f.properties as {
								id?: string;
							} | null;
							return props?.id === selectedOfficerId;
						}
					);

					if (
						officerFeature &&
						officerFeature.geometry.type === "Point"
					) {
						const currentPos = officerFeature.geometry
							.coordinates as [number, number];
						const end = incidentLocation;
						const url = `https://api.mapbox.com/directions/v5/mapbox/driving/${currentPos[0]},${currentPos[1]};${end[0]},${end[1]}?geometries=geojson&access_token=${token}`;

						try {
							const response = await fetch(url);
							const routeData = await response.json();

							if (
								routeData.routes &&
								routeData.routes.length > 0
							) {
								const route = routeData.routes[0];
								const coordinates = route.geometry.coordinates;

								// Update the route source with new coordinates
								const routeSource = map.current!.getSource(
									"selected-officer-route"
								) as mapboxgl.GeoJSONSource;
								if (routeSource) {
									routeSource.setData({
										type: "Feature",
										properties: {},
										geometry: {
											type: "LineString",
											coordinates: coordinates,
										},
									});
								}
							}
						} catch (error) {
							console.error("Error updating route:", error);
						}
					}
				}
			}

			animationFrameId = requestAnimationFrame(updateRoute);
		};

		animationFrameId = requestAnimationFrame(updateRoute);

		return () => {
			if (animationFrameId) {
				cancelAnimationFrame(animationFrameId);
			}
		};
	}, [selectedOfficerId, incidentLocation, policeOfficers]);

	useEffect(() => {
		console.log("[EmbeddedMap] useEffect started");
		console.log("[EmbeddedMap] incidentLocation:", incidentLocation);
		console.log("[EmbeddedMap] map.current:", map.current);
		console.log("[EmbeddedMap] initialized.current:", initialized.current);
		console.log(
			"[EmbeddedMap] mapContainer.current:",
			mapContainer.current
		);

		if (initialized.current) {
			console.log("[EmbeddedMap] Already initialized, skipping");
			return;
		}

		initialized.current = true;

		const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
		console.log("[EmbeddedMap] Mapbox token exists:", !!token);

		if (!token) {
			console.error("[EmbeddedMap] Mapbox token not found");
			return;
		}

		mapboxgl.accessToken = token;
		console.log("[EmbeddedMap] Mapbox accessToken set");

		const lng = incidentLocation
			? incidentLocation[0]
			: (BOBBY_DODD[0] + MERCEDES_BENZ[0]) / 2;
		const lat = incidentLocation
			? incidentLocation[1]
			: (BOBBY_DODD[1] + MERCEDES_BENZ[1]) / 2;
		const zoom = incidentLocation ? 16 : 14;
		const pitch = incidentLocation ? 65 : 45;
		console.log("[EmbeddedMap] Map center:", { lng, lat, zoom, pitch });

		try {
			map.current = new mapboxgl.Map({
				container: mapContainer.current!,
				style: "mapbox://styles/mapbox/dark-v11",
				center: [lng, lat],
				zoom: zoom,
				pitch: pitch,
				bearing: 30, // Rotate map by 30 degrees
				antialias: true,
				interactive: true, // Enable interaction for pan, rotate, and tilt
			});
			console.log("[EmbeddedMap] Map instance created successfully");
		} catch (error) {
			console.error("[EmbeddedMap] Error creating map:", error);
			return;
		}
		map.current.on("load", () => {
			console.log("[EmbeddedMap] Map loaded successfully");
			const layers = map.current!.getStyle().layers;
			let labelLayerId = "";

			for (let i = layers.length - 1; i >= 0; i--) {
				if (
					layers[i].type === "symbol" &&
					layers[i].layout!["text-field"]
				) {
					labelLayerId = layers[i].id;
					break;
				}
			}

			map.current!.addLayer(
				{
					id: "3d-buildings",
					source: "composite",
					"source-layer": "building",
					type: "fill-extrusion",
					minzoom: 13,
					paint: {
						"fill-extrusion-color": [
							"interpolate",
							["linear"],
							["get", "height"],
							0,
							"#2a2a2a",
							30,
							"#252525",
							50,
							"#202020",
							100,
							"#1a1a1a",
							150,
							"#151515",
							200,
							"#101010",
						],
						"fill-extrusion-height": [
							"interpolate",
							["linear"],
							["zoom"],
							13,
							0,
							13.5,
							["get", "height"],
						],
						"fill-extrusion-base": [
							"interpolate",
							["linear"],
							["zoom"],
							13,
							0,
							13.5,
							["get", "min_height"],
						],
						"fill-extrusion-opacity": 0.8,
					},
				},
				labelLayerId
			);

			// Add incident marker if location is provided, otherwise add route animation
			if (incidentLocation) {
				console.log("[EmbeddedMap] Adding incident marker");
				addIncidentMarker(map.current!, incidentLocation);
			} else {
				console.log("[EmbeddedMap] Adding route animation");
				addRouteToMap(map.current!);
			}

			// Add police officers if provided
			if (policeOfficers && policeOfficers.length > 0) {
				console.log("[EmbeddedMap] Adding police officers");
				addPoliceOfficers(
					map.current!,
					policeOfficers,
					onOfficerClick,
					() => policeOfficersRef.current
				);
			}
		});
		map.current.on("error", (e) => {
			console.error("[EmbeddedMap] Map error:", e);
		});

		return () => {
			console.log("[EmbeddedMap] Cleanup - removing map");
			if (map.current) {
				map.current.remove();
				map.current = null;
			}
			initialized.current = false;
		};
	}, []);

	return (
		<div
			ref={mapContainer}
			className="w-full h-full rounded-2xl"
			style={{ minHeight: "300px" }}
		/>
	);
};

export default EmbeddedMap;
