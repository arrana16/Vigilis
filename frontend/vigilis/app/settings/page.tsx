import { Navbar } from '../navigation';

export default function Settings() {
	return (
		<>
			<Navbar />
			<div className="min-h-screen bg-black pt-16">
				<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
					<h1 className="text-3xl font-bold text-white mb-6">
						Settings
					</h1>
					<p className="text-gray-400">
						Settings page - Coming soon
					</p>
				</div>
			</div>
		</>
	);
}
