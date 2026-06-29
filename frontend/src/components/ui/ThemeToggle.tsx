import { useTheme } from "../../hooks/useTheme";

const OPTIONS = [
  { value: "light" as const, label: "Светлая" },
  { value: "dark"  as const, label: "Тёмная" },
  { value: "system" as const, label: "Системная" },
];

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <select
      value={theme}
      onChange={(e) => setTheme(e.target.value as "light" | "dark" | "system")}
      className="text-xs rounded-md border border-gray-300 bg-white px-2 py-1 text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-400"
    >
      {OPTIONS.map(({ value, label }) => (
        <option key={value} value={value}>{label}</option>
      ))}
    </select>
  );
}
