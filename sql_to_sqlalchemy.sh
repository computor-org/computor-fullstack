#!/bin/bash

VAR="src/ctutor_backend/model/models_generated.py"
sqlacodegen postgresql://postgres:postgres_secret@localhost:5432/codeability > $VAR
echo "$(echo -n 'from typing import Text '; cat $VAR)" > $VAR