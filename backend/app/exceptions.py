class WorkflowNotFoundError(Exception):
    pass

class WorkflowValidationError(Exception):
    pass

class WorkflowModificationError(Exception):
    """Raised when there's an error modifying a workflow, such as referencing non-existent nodes."""
    pass 