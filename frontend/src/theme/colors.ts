export const colors = {
  navy: "#1B3A5C",
  navyDark: "#0a192f",
  navyLight: "#112240",
  navyLighter: "#1d3461",
  accent: "#E85D3A",
  accentLight: "#f07856",
  blue: "#2E6B9E",
  blueLight: "#5A9BD5",
  textPrimary: "#ccd6f6",
  textSecondary: "#8892b0",
  textBright: "#e6f1ff",
  success: "#64ffda",
  warning: "#ffd166",
  danger: "#ff6b6b",
} as const;

export const chartColors = [
  colors.accent,
  colors.success,
  colors.warning,
  colors.danger,
  colors.textSecondary,
  colors.accentLight,
  colors.blueLight,
] as const;

export const tooltipStyle = {
  background: "rgba(17,34,64,0.95)",
  border: "1px solid rgba(204,214,246,0.15)",
  borderRadius: 8,
  color: colors.textPrimary,
} as const;
