-- pandoc 过滤器：去掉 EPUB 转 GFM 时带出的 HTML 噪声
-- 图片和标题的属性、div/span 包装、指向书内文件或锚点的链接（只保留链接文字）；
-- figure 拆成「图片段落 + 图注段落」，避免输出 <figure> HTML

local function paras(blocks, out)
  for _, b in ipairs(blocks) do
    table.insert(out, b.t == "Plain" and pandoc.Para(b.content) or b)
  end
  return out
end

function Figure(el)
  return paras(el.caption.long, paras(el.content, {}))
end

local function bare(el)
  el.attributes = {}
  el.classes = {}
  el.identifier = ""
  return el
end

Image = bare
Header = bare

function Div(el)
  return el.content
end

function Span(el)
  return el.content
end

function Link(el)
  if not el.target:match("^%a[%w+.-]*:") then
    return el.content
  end
end
