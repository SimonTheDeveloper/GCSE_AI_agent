import '@testing-library/jest-dom';

if (!window.matchMedia) {
	window.matchMedia = ((query: string) => {
		return {
			matches: false,
			media: query,
			onchange: null,
			addListener: () => {},
			removeListener: () => {},
			addEventListener: () => {},
			removeEventListener: () => {},
			dispatchEvent: () => false,
		};
	}) as any;
}

if (!(globalThis as any).ResizeObserver) {
	class ResizeObserver {
		observe() {}
		unobserve() {}
		disconnect() {}
	}
	(globalThis as any).ResizeObserver = ResizeObserver;
}
