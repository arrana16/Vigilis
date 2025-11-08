'use client';

import React from 'react';
import Link from 'next/link';

const Navbar: React.FC = () => {
	return (
		<nav className="fixed top-0 left-0 right-0 z-50 bg-black bg-opacity-80 backdrop-blur-sm border-b border-gray-800">
			<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
				<div className="flex items-center justify-between h-16">
					{/* Logo/Brand */}
					<div className="flex-shrink-0">
						<Link href="/" className="text-white text-xl font-bold">
							Vigilis
						</Link>
					</div>

					{/* Navigation Links */}
					<div className="hidden md:block">
						<div className="ml-10 flex items-baseline space-x-4">
							<Link
								href="/"
								className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
							>
								Map
							</Link>
							<Link
								href="/dashboard"
								className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
							>
								Dashboard
							</Link>
							<Link
								href="/settings"
								className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
							>
								Settings
							</Link>
						</div>
					</div>

					{/* Mobile menu button */}
					<div className="md:hidden">
						<button
							type="button"
							className="text-gray-400 hover:text-white inline-flex items-center justify-center p-2 rounded-md focus:outline-none"
							aria-controls="mobile-menu"
							aria-expanded="false"
						>
							<span className="sr-only">Open main menu</span>
							{/* Icon */}
							<svg
								className="block h-6 w-6"
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
								aria-hidden="true"
							>
								<path
									strokeLinecap="round"
									strokeLinejoin="round"
									strokeWidth={2}
									d="M4 6h16M4 12h16M4 18h16"
								/>
							</svg>
						</button>
					</div>
				</div>
			</div>
		</nav>
	);
};

export default Navbar;
