library(shiny)
library(jsonlite)
library(httr2)

# ---------- Security + sandbox config ----------
ANTHROPIC_API_KEY <- Sys.getenv("ANTHROPIC_API_KEY")
if (ANTHROPIC_API_KEY == "") stop("Set ANTHROPIC_API_KEY")

MODEL <- Sys.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")
WORKSPACE_ROOT <- normalizePath(Sys.getenv("AGENT_WORKSPACE", "./workspace"), mustWork = FALSE)
dir.create(WORKSPACE_ROOT, recursive = TRUE, showWarnings = FALSE)

SKILLS_PROMPT <- paste(
  "You are a constrained coding assistant.",
  "Skills:",
  "1) Summarize files clearly before editing.",
  "2) Keep edits minimal and reversible.",
  "3) Never access files outside the tool sandbox.",
  "4) Do not browse external websites or fetch remote code.",
  sep = "\n"
)

safe_path <- function(rel_path) {
  candidate <- normalizePath(file.path(WORKSPACE_ROOT, rel_path), mustWork = FALSE)
  if (!startsWith(candidate, WORKSPACE_ROOT)) stop("Path escapes workspace sandbox")
  candidate
}

list_files <- function() {
  files <- list.files(WORKSPACE_ROOT, recursive = TRUE, all.files = FALSE)
  toJSON(list(files = files), auto_unbox = TRUE)
}

read_file <- function(path) {
  p <- safe_path(path)
  if (!file.exists(p)) return(toJSON(list(error = "file not found"), auto_unbox = TRUE))
  txt <- paste(readLines(p, warn = FALSE), collapse = "\n")
  toJSON(list(path = path, content = txt), auto_unbox = TRUE)
}

write_file <- function(path, content) {
  p <- safe_path(path)
  dir.create(dirname(p), recursive = TRUE, showWarnings = FALSE)
  writeLines(content, p)
  toJSON(list(ok = TRUE, path = path), auto_unbox = TRUE)
}

call_claude <- function(messages) {
  tools <- list(
    list(
      name = "list_files",
      description = "List relative files inside workspace sandbox.",
      input_schema = list(type = "object", properties = list())
    ),
    list(
      name = "read_file",
      description = "Read a UTF-8 text file from sandbox workspace.",
      input_schema = list(
        type = "object",
        properties = list(path = list(type = "string")),
        required = list("path")
      )
    ),
    list(
      name = "write_file",
      description = "Write text to a file in sandbox workspace.",
      input_schema = list(
        type = "object",
        properties = list(
          path = list(type = "string"),
          content = list(type = "string")
        ),
        required = list("path", "content")
      )
    )
  )

  body <- list(
    model = MODEL,
    max_tokens = 900,
    system = SKILLS_PROMPT,
    tools = tools,
    messages = messages
  )

  req <- request("https://api.anthropic.com/v1/messages") |>
    req_headers(
      "x-api-key" = ANTHROPIC_API_KEY,
      "anthropic-version" = "2023-06-01",
      "content-type" = "application/json"
    ) |>
    req_body_json(body, auto_unbox = TRUE) |>
    req_method("POST")

  resp <- req_perform(req)
  resp_body_json(resp)
}

run_agent_turn <- function(history) {
  messages <- lapply(history, function(m) {
    list(role = m$role, content = list(list(type = "text", text = m$content)))
  })

  for (i in 1:5) {
    out <- call_claude(messages)
    blocks <- out$content

    tool_block <- NULL
    text_parts <- c()
    for (b in blocks) {
      if (!is.null(b$type) && b$type == "tool_use") tool_block <- b
      if (!is.null(b$type) && b$type == "text") text_parts <- c(text_parts, b$text)
    }

    if (is.null(tool_block)) {
      return(paste(text_parts, collapse = "\n"))
    }

    tool_name <- tool_block$name
    input <- tool_block$input

    tool_output <- switch(
      tool_name,
      list_files = list_files(),
      read_file = read_file(input$path),
      write_file = write_file(input$path, input$content),
      toJSON(list(error = "unknown tool"), auto_unbox = TRUE)
    )

    messages <- append(messages, list(
      list(role = "assistant", content = blocks),
      list(
        role = "user",
        content = list(list(
          type = "tool_result",
          tool_use_id = tool_block$id,
          content = tool_output
        ))
      )
    ))
  }

  "Stopped after tool loop limit (5 turns)."
}

ui <- fluidPage(
  titlePanel("Claude-style Agent (R Shiny)"),
  tags$p("Sandbox root:", code(WORKSPACE_ROOT)),
  textAreaInput("prompt", "Prompt", rows = 5, placeholder = "Ask the agent to inspect or edit files..."),
  actionButton("send", "Send"),
  hr(),
  verbatimTextOutput("chat")
)

server <- function(input, output, session) {
  history <- reactiveVal(list())

  observeEvent(input$send, {
    h <- history()
    h[[length(h) + 1]] <- list(role = "user", content = input$prompt)
    answer <- run_agent_turn(h)
    h[[length(h) + 1]] <- list(role = "assistant", content = answer)
    history(h)
  })

  output$chat <- renderText({
    h <- history()
    if (length(h) == 0) return("No messages yet.")
    paste(vapply(h, function(m) paste0(toupper(m$role), ": ", m$content), character(1)), collapse = "\n\n")
  })
}

shinyApp(ui, server)
