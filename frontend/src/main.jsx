import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { ConfigProvider } from "antd";
import "antd/dist/reset.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ConfigProvider
      theme={{
        token: {
          fontFamily:
            "Roboto, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        },
        components: {
          Menu: {
            itemSelectedBg: "#FFF8DE",
            itemSelectedColor: "#000000",
            itemHoverBg: "#FFF8DE",
            itemHoverColor: "#000000",
            itemColor: "#FFFFFF",
          },
        },
      }}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>
);
