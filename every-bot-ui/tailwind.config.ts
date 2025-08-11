import type { Config } from 'tailwindcss'

const config: Config = {
	darkMode: ['class'],
	content: [
		'./src/**/*.{ts,tsx}',
	],
	theme: {
		extend: {
			colors: {
				primary: {
					500: '#6366f1'
				}
			}
		}
	},
	plugins: [require('tailwindcss-animate')]
}

export default config

