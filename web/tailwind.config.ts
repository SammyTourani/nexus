import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.tsx",
    "./app/**/*.ts",
    "./components/**/*.tsx",
    "./components/**/*.ts",
  ],
};

export default config;
