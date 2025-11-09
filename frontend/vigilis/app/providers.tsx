"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode, useEffect, useState } from "react";

const API_URL = "https://vigilis.onrender.com";
// = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
const WS_URL = "https://vigilis.onrender.com";
// = process.env.NEXT_PUBLIC_API_BASE || API_URL.replace(/^http/, "ws");

export function Providers({ children }: { children: ReactNode }) {
	const [queryClient] = useState(
		() =>
			new QueryClient({
				defaultOptions: {
					queries: {
						staleTime: 60_000,
						refetchOnWindowFocus: false,
					},
				},
			})
	);

	useEffect(() => {
		// Single WebSocket for broadcast invalidations (pattern: frontend-context)
		const socket = new WebSocket(`${WS_URL}/ws`);

		socket.onopen = () => console.log("✅ Core WS connected");
		socket.onmessage = (evt) => {
			if (evt.data === "data_updated") {
				console.log("🔄 Invalidate incident queries");
				queryClient.invalidateQueries();
			}
		};
		socket.onerror = (err) => console.error("❌ Core WS error", err);
		socket.onclose = () => console.log("🔌 Core WS closed");

		return () => socket.close();
	}, [queryClient]);

	return (
		<QueryClientProvider client={queryClient}>
			{children}
		</QueryClientProvider>
	);
}
