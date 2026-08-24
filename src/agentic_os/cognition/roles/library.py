from.role import Role
LIBRARY = {
  "director": Role(name="director", permissions=["propose_intent"], forbidden_tools=[]),
  "operator": Role(name="operator", permissions=["execute"], forbidden_tools=["gmail_send"]),
  "auditor": Role(name="auditor", permissions=["read"], forbidden_tools=["*"])
}
