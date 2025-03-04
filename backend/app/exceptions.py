class WorkflowNotFoundError(Exception):
    """Raised when a workflow file is not found."""
    pass

class WorkflowValidationError(Exception):
    """Raised when error happens while opening a workflow file."""
    pass

class WorkflowModificationError(Exception):
    """Raised when there's an error modifying a workflow, such as referencing non-existent nodes."""
    pass 