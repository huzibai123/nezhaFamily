/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            /* ===== 品牌色系 ===== */
            colors: {
                /* 主色：温暖珊瑚色，用于 CTA、强调、点赞 */
                primary: {
                    50: "#FFF0F0",
                    100: "#FFDEDE",
                    200: "#FFC4C4",
                    300: "#FFA0A0",
                    400: "#FF8383",
                    500: "#FF6B6B",
                    600: "#E04F4F",
                    700: "#C13A3A",
                    800: "#9E2828",
                    900: "#7A1C1C",
                },
                /* 辅助色：柔和蓝绿，用于成功状态、次要操作 */
                secondary: {
                    50: "#E6F9F4",
                    100: "#C2F0E6",
                    200: "#99E7D5",
                    300: "#66DCC1",
                    400: "#33D0AE",
                    500: "#00B894",
                    600: "#009A7C",
                    700: "#007D64",
                    800: "#00604D",
                    900: "#004335",
                },
                /* 中性色：暖灰系，用于背景、文字层级 */
                warm: {
                    50: "#FCFCFA",
                    100: "#FAFAF7",
                    200: "#F5F2ED",
                    300: "#EDE8E0",
                    400: "#D5CFC5",
                    500: "#B8B0A4",
                    600: "#9A9184",
                    700: "#7D7568",
                    800: "#60594E",
                    900: "#453E35",
                },
            },

            /* ===== 自定义字体大小（中文优化，稍大字号提升可读性） ===== */
            fontSize: {
                hero: [
                    "48px",
                    { lineHeight: "1.1", letterSpacing: "-0.02em", fontWeight: "700" },
                ],
                section: [
                    "32px",
                    { lineHeight: "1.2", letterSpacing: "-0.01em", fontWeight: "600" },
                ],
                headline: [
                    "20px",
                    { lineHeight: "1.3", fontWeight: "600" },
                ],
                subhead: [
                    "18px",
                    { lineHeight: "1.4", fontWeight: "500" },
                ],
                body: [
                    "16px",
                    { lineHeight: "1.7" },
                ],
                caption: [
                    "13px",
                    { lineHeight: "1.5" },
                ],
            },

            /* ===== 自定义间距 ===== */
            spacing: {
                section: "112px",
                group: "64px",
                18: "72px",
                22: "88px",
                30: "120px",
            },

            /* ===== 柔和圆角系统 ===== */
            borderRadius: {
                xs: "6px",
                sm: "10px",
                md: "14px",
                lg: "18px",
                xl: "24px",
                full: "9999px",
            },

            /* ===== 中文字体栈（优先中文排版字体） ===== */
            fontFamily: {
                sans: [
                    '"PingFang SC"',
                    '"Microsoft YaHei"',
                    '"Hiragino Sans GB"',
                    '"Noto Sans CJK SC"',
                    "system-ui",
                    "-apple-system",
                    "BlinkMacSystemFont",
                    '"Segoe UI"',
                    "Roboto",
                    "sans-serif",
                ],
                heading: [
                    '"PingFang SC"',
                    '"Microsoft YaHei"',
                    '"Hiragino Sans GB"',
                    "system-ui",
                    "-apple-system",
                    "sans-serif",
                ],
                mono: [
                    "ui-monospace",
                    '"Cascadia Code"',
                    '"Source Code Pro"',
                    "Menlo",
                    "Consolas",
                    "monospace",
                ],
            },

            /* ===== 柔和阴影系统 ===== */
            boxShadow: {
                card:
                    "0 2px 16px rgba(69, 62, 53, 0.06), 0 1px 4px rgba(69, 62, 53, 0.04)",
                "card-hover":
                    "0 8px 30px rgba(69, 62, 53, 0.10), 0 2px 8px rgba(69, 62, 53, 0.06)",
                nav: "0 1px 3px rgba(69, 62, 53, 0.06)",
                button: "0 2px 8px rgba(255, 107, 107, 0.25)",
            },
        },
    },
    plugins: [],
};
