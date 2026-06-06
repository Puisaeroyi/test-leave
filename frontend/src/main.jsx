import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { App as AntdApp, ConfigProvider } from "antd";
import { antdTheme } from "./styles/antd-theme";
import "antd/dist/reset.css";
import "./styles/tokens.css";
import "./styles/base.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ConfigProvider theme={antdTheme}>
      <AntdApp>
        <App />
      </AntdApp>
    </ConfigProvider>
  </React.StrictMode>
);
