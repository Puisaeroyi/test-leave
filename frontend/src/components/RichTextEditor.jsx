import { useEffect, useRef } from "react";
import { Button, Space, Tooltip } from "antd";
import {
  AlignCenterOutlined,
  AlignLeftOutlined,
  AlignRightOutlined,
  BoldOutlined,
  EnterOutlined,
  ItalicOutlined,
  LinkOutlined,
  OrderedListOutlined,
  PictureOutlined,
  StrikethroughOutlined,
  UnderlineOutlined,
  UnorderedListOutlined,
} from "@ant-design/icons";

const imageFileToDataUrl = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });

const insertHtml = (html) => {
  document.execCommand("insertHTML", false, html);
};

export default function RichTextEditor({ value = "", onChange, placeholder }) {
  const editorRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (editorRef.current && editorRef.current.innerHTML !== value) {
      editorRef.current.innerHTML = value || "";
    }
  }, [value]);

  const emitChange = () => {
    onChange?.(editorRef.current?.innerHTML || "");
  };

  const runCommand = (command, commandValue = null) => {
    editorRef.current?.focus();
    document.execCommand(command, false, commandValue);
    emitChange();
  };

  const insertLink = () => {
    const url = window.prompt("Enter link URL");
    if (!url) return;
    runCommand("createLink", url);
  };

  const insertDivider = () => {
    editorRef.current?.focus();
    insertHtml("<hr>");
    emitChange();
  };

  const insertQuote = () => {
    editorRef.current?.focus();
    insertHtml("<blockquote>Quote text...</blockquote>");
    emitChange();
  };

  const insertImageFile = async (file) => {
    if (!file?.type?.startsWith("image/")) return;
    const dataUrl = await imageFileToDataUrl(file);
    insertHtml(`<figure><img src="${dataUrl}" alt="Pasted image"><figcaption>Image caption</figcaption></figure>`);
    emitChange();
  };

  const handlePaste = async (event) => {
    const image = Array.from(event.clipboardData?.files || []).find((file) => file.type.startsWith("image/"));
    if (image) {
      event.preventDefault();
      await insertImageFile(image);
    }
  };

  const handleDrop = async (event) => {
    const image = Array.from(event.dataTransfer?.files || []).find((file) => file.type.startsWith("image/"));
    if (image) {
      event.preventDefault();
      editorRef.current?.focus();
      await insertImageFile(image);
    }
  };

  const handleImageSelect = async (event) => {
    const file = event.target.files?.[0];
    await insertImageFile(file);
    event.target.value = "";
  };

  return (
    <div className="rich-text-editor">
      <Space wrap className="rich-text-editor__toolbar">
        <Tooltip title="Bold"><Button icon={<BoldOutlined />} onClick={() => runCommand("bold")} /></Tooltip>
        <Tooltip title="Italic"><Button icon={<ItalicOutlined />} onClick={() => runCommand("italic")} /></Tooltip>
        <Tooltip title="Underline"><Button icon={<UnderlineOutlined />} onClick={() => runCommand("underline")} /></Tooltip>
        <Tooltip title="Strike"><Button icon={<StrikethroughOutlined />} onClick={() => runCommand("strikeThrough")} /></Tooltip>
        <Tooltip title="Heading"><Button onClick={() => runCommand("formatBlock", "h2")}>H2</Button></Tooltip>
        <Tooltip title="Subheading"><Button onClick={() => runCommand("formatBlock", "h3")}>H3</Button></Tooltip>
        <Tooltip title="Paragraph"><Button onClick={() => runCommand("formatBlock", "p")}>P</Button></Tooltip>
        <Tooltip title="Align left"><Button icon={<AlignLeftOutlined />} onClick={() => runCommand("justifyLeft")} /></Tooltip>
        <Tooltip title="Align center"><Button icon={<AlignCenterOutlined />} onClick={() => runCommand("justifyCenter")} /></Tooltip>
        <Tooltip title="Align right"><Button icon={<AlignRightOutlined />} onClick={() => runCommand("justifyRight")} /></Tooltip>
        <Tooltip title="Justify"><Button onClick={() => runCommand("justifyFull")}>Justify</Button></Tooltip>
        <Tooltip title="Bulleted list"><Button icon={<UnorderedListOutlined />} onClick={() => runCommand("insertUnorderedList")} /></Tooltip>
        <Tooltip title="Numbered list"><Button icon={<OrderedListOutlined />} onClick={() => runCommand("insertOrderedList")} /></Tooltip>
        <Tooltip title="Quote"><Button onClick={insertQuote}>Quote</Button></Tooltip>
        <Tooltip title="Link"><Button icon={<LinkOutlined />} onClick={insertLink} /></Tooltip>
        <Tooltip title="Divider"><Button icon={<EnterOutlined />} onClick={insertDivider} /></Tooltip>
        <Tooltip title="Insert image"><Button icon={<PictureOutlined />} onClick={() => fileInputRef.current?.click()} /></Tooltip>
      </Space>
      <div
        ref={editorRef}
        className="rich-text-editor__surface rich-content"
        contentEditable
        data-placeholder={placeholder}
        onBlur={emitChange}
        onInput={emitChange}
        onPaste={handlePaste}
        onDrop={handleDrop}
        suppressContentEditableWarning
      />
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        style={{ display: "none" }}
        onChange={handleImageSelect}
      />
    </div>
  );
}
