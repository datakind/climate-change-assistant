import os

note_message = "The accurate cost of the assistant is unpredictable, especially when code interpreter, retrieval and call tools are being used. Furthermore, the assistant intelligently chooses which context from the thread to include when calling the model which means the price could be higher."

assistant_id = os.environ.get("ASSISTANT_ID")
assistant_model = os.environ.get("MODEL")
is_dev = os.environ.get("IS_DEV") == "true"
