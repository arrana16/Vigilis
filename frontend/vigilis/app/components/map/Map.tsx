"use client";

import React, { useRef, useEffect, useState } from "react";
import mapboxgl from "mapbox-gl";
import * as turf from "@turf/turf";
import "mapbox-gl/dist/mapbox-gl.css";

// Map component props
interface MapProps {
	incidentLocation?: [number, number]; // [lng, lat] - if provided, shows incident view
}

// Stadium coordinates
const BOBBY_DODD = [-84.3933, 33.7726]; // Bobby Dodd Stadium (Georgia Tech)
const MERCEDES_BENZ = [-84.4008, 33.7552]; // Mercedes-Benz Stadium

// Easing function for smooth ease-in-ease-out
function easeInOutCubic(t: number): number {
	return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

// Function to add route to map with cinematic animation
async function addRouteToMap(map: mapboxgl.Map) {
	const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

	if (!token) {
		console.error("Mapbox token not found");
		return;
	}

	try {
		// Fetch route from Mapbox Directions API
		const url = `https://api.mapbox.com/directions/v5/mapbox/driving/${BOBBY_DODD[0]},${BOBBY_DODD[1]};${MERCEDES_BENZ[0]},${MERCEDES_BENZ[1]}?steps=true&geometries=geojson&access_token=${token}`;

		const response = await fetch(url);
		const data = await response.json();

		if (!data.routes || data.routes.length === 0) {
			console.error("No route found");
			return;
		}

		const route = data.routes[0];
		const routeCoordinates = route.geometry.coordinates;

		// Create route as a Turf LineString for distance calculations
		const routeLine = turf.lineString(routeCoordinates);
		const routeDistance = turf.length(routeLine, { units: "kilometers" });

		// Add source for the route with line-gradient support
		map.addSource("route", {
			type: "geojson",
			lineMetrics: true, // Enable line-gradient
			data: {
				type: "Feature",
				properties: {},
				geometry: {
					type: "LineString",
					coordinates: routeCoordinates,
				},
			},
		});

		// Add the main route line with gradient
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
					"#ff0000", // Red for revealed portion
					0,
					"rgba(255, 0, 0, 0)", // Transparent for unrevealed
				],
			},
		});

		// Add glow effect
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

		// Add markers
		addStadiumMarkers(map);

		// Cinematic animation setup
		const animationDuration = 5000; // 5 seconds
		const startTime = Date.now();
		// Animation frame handle intentionally unused (kept for future cancellation logic)
		let animationFrame: number | undefined;

		// Camera smoothing via LERP
		let cameraPosition: [number, number] | null = null;
		const lerpFactor = 0.4; // Higher value for tighter following

		function animateRoute() {
			const elapsed = Date.now() - startTime;
			const linearProgress = Math.min(elapsed / animationDuration, 1);

			// Apply easing function for smooth start and end
			const progress = easeInOutCubic(linearProgress);

			// Update line gradient to reveal the route progressively
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

			// Calculate the current point along the route using Turf
			const distanceAlongRoute = progress * routeDistance;
			const currentPoint = turf.along(routeLine, distanceAlongRoute, {
				units: "kilometers",
			});
			const currentCoords = currentPoint.geometry.coordinates as [
				number,
				number
			];

			// Calculate camera position with offset for better view
			const targetPosition = currentCoords;

			// Apply LERP for smooth camera movement
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

			// Update camera to follow the route with closer zoom
			map.easeTo({
				center: cameraPosition,
				zoom: 15, // Closer zoom level
				duration: 0,
				pitch: 50, // Slightly higher pitch for more dramatic view
				bearing: progress * 30, // Slowly rotate for cinematic effect
			});

			if (linearProgress < 1) {
				animationFrame = requestAnimationFrame(animateRoute);
			}
		}

		// Start animation after a short delay
		setTimeout(() => {
			animationFrame = requestAnimationFrame(animateRoute);
		}, 500);
	} catch (error) {
		console.error("Error fetching route:", error);
	}
}

// Function to add stadium markers
function addStadiumMarkers(map: mapboxgl.Map) {
	// Bobby Dodd Stadium marker
	const boddyMarker = document.createElement("div");
	boddyMarker.className = "marker";
	boddyMarker.style.width = "32px";
	boddyMarker.style.height = "32px";
	boddyMarker.style.backgroundImage =
		'url("data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22 fill=%2300ff00%22%3E%3Ccircle cx=%2212%22 cy=%2212%22 r=%2210%22/%3E%3C/svg%3E")';
	boddyMarker.style.backgroundSize = "contain";
	boddyMarker.style.cursor = "pointer";

	new mapboxgl.Marker(boddyMarker)
		.setLngLat(BOBBY_DODD as [number, number])
		.setPopup(new mapboxgl.Popup().setText("Bobby Dodd Stadium"))
		.addTo(map);

	// Mercedes-Benz Stadium marker
	const benzMarker = document.createElement("div");
	benzMarker.className = "marker";
	benzMarker.style.width = "32px";
	benzMarker.style.height = "32px";
	benzMarker.style.backgroundImage =
		'url("data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22 fill=%2300ffff%22%3E%3Ccircle cx=%2212%22 cy=%2212%22 r=%2210%22/%3E%3C/svg%3E")';
	benzMarker.style.backgroundSize = "contain";
	benzMarker.style.cursor = "pointer";

	new mapboxgl.Marker(benzMarker)
		.setLngLat(MERCEDES_BENZ as [number, number])
		.setPopup(new mapboxgl.Popup().setText("Mercedes-Benz Stadium"))
		.addTo(map);
}

// Function to add flashing incident marker
function addIncidentMarker(map: mapboxgl.Map, location: [number, number]) {
	// Create a circle feature at the incident location
	// We'll use circle layers to make it appear on the ground with proper perspective
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
}

const Map: React.FC<MapProps> = ({ incidentLocation }) => {
	const mapContainer = useRef<HTMLDivElement>(null);
	const map = useRef<mapboxgl.Map | null>(null);
	// Center between Bobby Dodd and Mercedes-Benz stadiums by default
	const [lng, setLng] = useState(
		incidentLocation
			? incidentLocation[0]
			: (BOBBY_DODD[0] + MERCEDES_BENZ[0]) / 2
	);
	const [lat, setLat] = useState(
		incidentLocation
			? incidentLocation[1]
			: (BOBBY_DODD[1] + MERCEDES_BENZ[1]) / 2
	);
	const [zoom, setZoom] = useState(incidentLocation ? 16 : 14);
	const [pitch, setPitch] = useState(incidentLocation ? 45 : 30);

	useEffect(() => {
		// Initialize map when component mounts
		if (map.current) return;

		// Note: You'll need to set your Mapbox access token
		// Get a free token at https://account.mapbox.com/auth/signup/
		const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

		if (!token) {
			console.error(
				"Mapbox token not found. Please set NEXT_PUBLIC_MAPBOX_TOKEN in your .env.local file"
			);
			return;
		}

		mapboxgl.accessToken = token;

		map.current = new mapboxgl.Map({
			container: mapContainer.current!,
			style: "mapbox://styles/mapbox/dark-v11",
			center: [lng, lat],
			zoom: zoom,
			pitch: pitch,
			bearing: 0,
			antialias: true,
		});

		// Add 3D building layer when map loads
		map.current.on("load", () => {
			const layers = map.current!.getStyle().layers;
			let labelLayerId = "";

			for (let i = layers.length - 1; i >= 0; i--) {
				const layer = layers[i] as mapboxgl.AnyLayer;
				if (layer.type === "symbol") {
					const layout = (
						layer as unknown as {
							layout?: { [k: string]: unknown };
						}
					).layout;
					if (layout && typeof layout["text-field"] !== "undefined") {
						labelLayerId = layer.id;
						break;
					}
				}
			}

			// Add 3D building extrusion layer with enhanced visuals
			map.current!.addLayer(
				{
					id: "3d-buildings",
					source: "composite",
					"source-layer": "building",
					type: "fill-extrusion",
					minzoom: 13,
					paint: {
						// Use color based on building height for better visualization - darker gray tones
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
							250,
							"#0d0d0d",
							300,
							"#0a0a0a",
							400,
							"#050505",
						],
						// Dynamic height based on zoom level
						"fill-extrusion-height": [
							"interpolate",
							["linear"],
							["zoom"],
							13,
							0,
							13.5,
							["get", "height"],
							21,
							["get", "height"],
						],
						// Base height for proper 3D effect
						"fill-extrusion-base": [
							"interpolate",
							["linear"],
							["zoom"],
							13,
							0,
							13.5,
							["get", "min_height"],
							21,
							["get", "min_height"],
						],
						// Better opacity for depth perception
						"fill-extrusion-opacity": [
							"interpolate",
							["linear"],
							["zoom"],
							13,
							0.5,
							16,
							0.8,
						],
					},
				},
				labelLayerId
			);

			// Add roof top highlights for depth
			map.current!.addLayer(
				{
					id: "3d-buildings-roof",
					source: "composite",
					"source-layer": "building",
					type: "fill",
					minzoom: 14,
					paint: {
						"fill-color": [
							"interpolate",
							["linear"],
							["get", "height"],
							0,
							"#3a3a3a",
							30,
							"#353535",
							50,
							"#303030",
							100,
							"#2a2a2a",
							150,
							"#252525",
							200,
							"#202020",
							250,
							"#1a1a1a",
							300,
							"#151515",
							400,
							"#101010",
						],
						"fill-opacity": [
							"interpolate",
							["linear"],
							["pitch"],
							0,
							0,
							30,
							0.3,
							60,
							0.6,
						],
					},
				},
				labelLayerId
			);

			// Add building edge shadows for depth perception
			map.current!.addLayer(
				{
					id: "3d-buildings-shadow",
					source: "composite",
					"source-layer": "building",
					type: "line",
					minzoom: 13,
					paint: {
						"line-color": "#0a0a0a",
						"line-width": [
							"interpolate",
							["linear"],
							["zoom"],
							13,
							0.5,
							15,
							1,
							17,
							2.5,
						],
						"line-opacity": [
							"interpolate",
							["linear"],
							["pitch"],
							0,
							0.1,
							45,
							0.5,
							85,
							0.7,
						],
					},
				},
				labelLayerId
			);

			// Add subtle building border for clarity
			map.current!.addLayer(
				{
					id: "3d-buildings-border",
					source: "composite",
					"source-layer": "building",
					type: "line",
					minzoom: 15,
					paint: {
						"line-color": "#333",
						"line-width": [
							"interpolate",
							["linear"],
							["zoom"],
							15,
							0.5,
							18,
							1.5,
						],
						"line-opacity": 0.3,
					},
				},
				labelLayerId
			);

			// Add incident marker if location is provided, otherwise add route animation
			if (incidentLocation) {
				addIncidentMarker(map.current!, incidentLocation);
			} else {
				addRouteToMap(map.current!);
			}
		});

		// Update state when map moves
		map.current.on("move", () => {
			setLng(Number(map.current!.getCenter().lng.toFixed(4)));
			setLat(Number(map.current!.getCenter().lat.toFixed(4)));
			setZoom(Number(map.current!.getZoom().toFixed(2)));
			setPitch(Number(map.current!.getPitch().toFixed(0)));
		});

		return () => {
			if (map.current) {
				map.current.remove();
			}
		};
		// Dependencies intentionally omitted to mimic initial mount only behavior.
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	// Handle tilt with arrow keys
	useEffect(() => {
		const handleKeyDown = (e: KeyboardEvent) => {
			if (!map.current) return;

			const currentPitch = map.current.getPitch();

			switch (e.key) {
				case "ArrowUp":
					e.preventDefault();
					map.current.setPitch(Math.min(currentPitch + 5, 85));
					break;
				case "ArrowDown":
					e.preventDefault();
					map.current.setPitch(Math.max(currentPitch - 5, 0));
					break;
				case "ArrowLeft":
					map.current.setBearing(map.current.getBearing() - 10);
					break;
				case "ArrowRight":
					map.current.setBearing(map.current.getBearing() + 10);
					break;
			}
		};

		window.addEventListener("keydown", handleKeyDown);
		return () => window.removeEventListener("keydown", handleKeyDown);
	}, []);

	// Handle Shift + left click to tilt
	useEffect(() => {
		const handleMouseDown = (e: MouseEvent) => {
			if (!map.current || !mapContainer.current) return;

			// Check if Shift is pressed and it's a left click
			if (e.shiftKey && e.button === 0) {
				e.preventDefault();
				const startY = e.clientY;
				const startPitch = map.current.getPitch();

				const handleMouseMove = (moveEvent: MouseEvent) => {
					const deltaY = moveEvent.clientY - startY;
					// Convert pixel movement to pitch change (10 pixels = 1 degree)
					// Flipped: drag down to increase tilt, drag up to decrease tilt
					const pitchChange = -deltaY / 10;
					const newPitch = Math.max(
						0,
						Math.min(85, startPitch + pitchChange)
					);
					map.current!.setPitch(newPitch);
				};

				const handleMouseUp = () => {
					window.removeEventListener("mousemove", handleMouseMove);
					window.removeEventListener("mouseup", handleMouseUp);
				};

				window.addEventListener("mousemove", handleMouseMove);
				window.addEventListener("mouseup", handleMouseUp);
			}
		};

		if (mapContainer.current) {
			mapContainer.current.addEventListener("mousedown", handleMouseDown);
			return () => {
				if (mapContainer.current) {
					mapContainer.current.removeEventListener(
						"mousedown",
						handleMouseDown
					);
				}
			};
		}
	}, []);

	return (
		<div className="w-full h-screen flex flex-col">
			<div ref={mapContainer} className="w-full flex-1" />

			{/* Controls and Info */}
			<div className="absolute top-4 left-4 bg-white bg-opacity-90 p-4 rounded-lg shadow-lg z-10">
				<div className="text-sm space-y-2">
					<p className="font-semibold text-gray-800">
						Atlanta 3D Map
					</p>
					<p className="text-gray-600">Longitude: {lng}</p>
					<p className="text-gray-600">Latitude: {lat}</p>
					<p className="text-gray-600">Zoom: {zoom}</p>
					<p className="text-gray-600">Tilt: {pitch}°</p>
				</div>
			</div>

			{/* Instructions */}
			<div className="absolute bottom-4 left-4 bg-white bg-opacity-90 p-4 rounded-lg shadow-lg z-10">
				<div className="text-xs space-y-1 text-gray-700">
					<p className="font-semibold">Controls:</p>
					<p>🖱️ Drag to pan</p>
					<p>🔄 Right-click + drag to rotate</p>
					<p>📏 Scroll to zoom</p>
					<p>⬆️ Arrow Up/Down - Tilt</p>
					<p>⬅️ Arrow Left/Right - Rotate</p>
					<p>⬇️ Shift + Drag Down - Tilt</p>
				</div>
			</div>

			{/* Tilt Controls */}
			<div className="absolute bottom-4 right-4 bg-white bg-opacity-90 p-4 rounded-lg shadow-lg z-10 space-y-2">
				<button
					onClick={() => {
						if (map.current) {
							map.current.setPitch(
								Math.min(map.current.getPitch() + 5, 85)
							);
						}
					}}
					className="block w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm font-medium"
				>
					⬆️ Tilt Up
				</button>
				<button
					onClick={() => {
						if (map.current) {
							map.current.setPitch(
								Math.max(map.current.getPitch() - 5, 0)
							);
						}
					}}
					className="block w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm font-medium"
				>
					⬇️ Tilt Down
				</button>
				<button
					onClick={() => {
						if (map.current) {
							map.current.setPitch(0);
							map.current.setBearing(0);
						}
					}}
					className="block w-full px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm font-medium"
				>
					🔄 Reset View
				</button>
			</div>
		</div>
	);
};

export default Map;
