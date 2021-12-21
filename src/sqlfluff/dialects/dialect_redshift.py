"""The Amazon Redshift dialect.

This is based on postgres dialect, since it was initially based off of Postgres 8.
We should monitor in future and see if it should be rebased off of ANSI
"""

from sqlfluff.core.parser import (
    OneOf,
    AnyNumberOf,
    Ref,
    Sequence,
    Bracketed,
    BaseSegment,
    Delimited,
    Nothing,
    OptionallyBracketed,
)

from sqlfluff.core.dialects import load_raw_dialect

from sqlfluff.dialects.dialect_redshift_keywords import (
    redshift_reserved_keywords,
    redshift_unreserved_keywords,
)


postgres_dialect = load_raw_dialect("postgres")
ansi_dialect = load_raw_dialect("ansi")

redshift_dialect = postgres_dialect.copy_as("redshift")

# Set Keywords
redshift_dialect.sets("unreserved_keywords").clear()
redshift_dialect.sets("unreserved_keywords").update(
    [n.strip().upper() for n in redshift_unreserved_keywords.split("\n")]
)

redshift_dialect.sets("reserved_keywords").clear()
redshift_dialect.sets("reserved_keywords").update(
    [n.strip().upper() for n in redshift_reserved_keywords.split("\n")]
)

redshift_dialect.sets("bare_functions").clear()
redshift_dialect.sets("bare_functions").update(["current_date", "sysdate"])

redshift_dialect.replace(WellKnownTextGeometrySegment=Nothing())


@redshift_dialect.segment(replace=True)
class DatePartFunctionNameSegment(BaseSegment):
    """DATEADD function name segment.

    Override to support DATEDIFF as well
    """

    type = "function_name"
    match_grammar = OneOf("DATEADD", "DATEDIFF")


@redshift_dialect.segment(replace=True)
class FunctionSegment(BaseSegment):
    """A scalar or aggregate function.

    Revert back to the ANSI definition to support ignore nulls
    """

    type = "function"
    match_grammar = ansi_dialect.get_segment("FunctionSegment").match_grammar.copy()


@redshift_dialect.segment()
class ColumnEncodingSegment(BaseSegment):
    """ColumnEncoding segment.

    Indicates column compression encoding.

    As specified by: https://docs.aws.amazon.com/redshift/latest/dg/c_Compression_encodings.html
    """

    type = "column_encoding_segment"

    match_grammar = OneOf(
        "RAW",
        "AZ64",
        "BYTEDICT",
        "DELTA",
        "DELTA32K",
        "LZO",
        "MOSTLY8",
        "MOSTLY16",
        "MOSTLY32",
        "RUNLENGTH",
        "TEXT255",
        "TEXT32K",
        "ZSTD",
    )


@redshift_dialect.segment()
class ColumnAttributeSegment(BaseSegment):
    """Redshift specific column attributes.

    As specified in https://docs.aws.amazon.com/redshift/latest/dg/r_CREATE_TABLE_NEW.html
    """

    type = "column_attribute_segment"

    match_grammar = AnyNumberOf(
        Sequence("DEFAULT", Ref("ExpressionSegment")),
        Sequence(
            "IDENTITY",
            Bracketed(Delimited(Ref("NumericLiteralSegment"))),
        ),
        Sequence(
            "GENERATED",
            "BY",
            "DEFAULT",
            "AS",
            "IDENTITY",
            Bracketed(Delimited(Ref("NumericLiteralSegment"))),
        ),
        Sequence("ENCODE", Ref("ColumnEncodingSegment")),
        "DISTKEY",
        "SORTKEY",
        Sequence("COLLATE", OneOf("CASE_SENSITIVE", "CASE_INSENSITIVE")),
    )


@redshift_dialect.segment(replace=True)
class ColumnConstraintSegment(BaseSegment):
    """Redshift specific column constraints.

    As specified in https://docs.aws.amazon.com/redshift/latest/dg/r_CREATE_TABLE_NEW.html
    """

    type = "column_constraint_segment"

    match_grammar = AnyNumberOf(
        OneOf(Sequence("NOT", "NULL"), "NULL"),
        OneOf("UNIQUE", Sequence("PRIMARY", "KEY")),
        Sequence(
            "REFERENCES",
            Ref("TableReferenceSegment"),
            Bracketed(Ref("ColumnReferenceSegment"), optional=True),
        ),
    )


@redshift_dialect.segment()
class TableAttributeSegment(BaseSegment):
    """Redshift specific table attributes.

    As specified in https://docs.aws.amazon.com/redshift/latest/dg/r_CREATE_TABLE_NEW.html
    """

    type = "table_constraint_segment"

    match_grammar = AnyNumberOf(
        Sequence("DISTSTYLE", OneOf("AUTO", "EVEN", "KEY", "ALL"), optional=True),
        Sequence("DISTKEY", Bracketed(Ref("ColumnReferenceSegment")), optional=True),
        OneOf(
            Sequence(
                OneOf("COMPOUND", "INTERLEAVED", optional=True),
                "SORTKEY",
                Bracketed(Delimited(Ref("ColumnReferenceSegment"))),
            ),
            Sequence("SORTKEY", "AUTO"),
            optional=True,
        ),
        Sequence("ENCODE", "AUTO", optional=True),
    )


@redshift_dialect.segment(replace=True)
class TableConstraintSegment(BaseSegment):
    """Redshift specific table constraints.

    As specified in https://docs.aws.amazon.com/redshift/latest/dg/r_CREATE_TABLE_NEW.html
    """

    type = "table_constraint_segment"

    match_grammar = AnyNumberOf(
        Sequence("UNIQUE", Bracketed(Delimited(Ref("ColumnReferenceSegment")))),
        Sequence(
            "PRIMARY",
            "KEY",
            Bracketed(Delimited(Ref("ColumnReferenceSegment"))),
        ),
        Sequence(
            "FOREIGN",
            "KEY",
            Bracketed(Delimited(Ref("ColumnReferenceSegment"))),
            "REFERENCES",
            Ref("TableReferenceSegment"),
            Sequence(Bracketed(Ref("ColumnReferenceSegment"))),
        ),
    )


@redshift_dialect.segment(replace=True)
class LikeOptionSegment(BaseSegment):
    """Like Option Segment.

    As specified in https://docs.aws.amazon.com/redshift/latest/dg/r_CREATE_TABLE_NEW.html
    """

    type = "like_option_segment"

    match_grammar = Sequence(OneOf("INCLUDING", "EXCLUDING"), "DEFAULTS")


@redshift_dialect.segment(replace=True)
class CreateTableStatementSegment(BaseSegment):
    """A `CREATE TABLE` statement.

    As specified in https://docs.aws.amazon.com/redshift/latest/dg/r_CREATE_TABLE_NEW.html
    """

    type = "create_table_statement"

    match_grammar = Sequence(
        "CREATE",
        Ref.keyword("LOCAL", optional=True),
        Ref("TemporaryGrammar", optional=True),
        "TABLE",
        Ref("IfNotExistsGrammar", optional=True),
        Ref("TableReferenceSegment"),
        Bracketed(
            OneOf(
                # Columns and comment syntax:
                Delimited(
                    Sequence(
                        Ref("ColumnReferenceSegment"),
                        Ref("DatatypeSegment"),
                        AnyNumberOf(Ref("ColumnAttributeSegment"), optional=True),
                        AnyNumberOf(Ref("ColumnConstraintSegment"), optional=True),
                    ),
                    Ref("TableConstraintSegment", optional=True),
                ),
                Sequence(
                    "LIKE",
                    Ref("TableReferenceSegment"),
                    AnyNumberOf(Ref("LikeOptionSegment"), optional=True),
                ),
            )
        ),
        Sequence("BACKUP", OneOf("YES", "NO", optional=True), optional=True),
        AnyNumberOf(Ref("TableAttributeSegment"), optional=True),
    )


@redshift_dialect.segment(replace=True)
class InsertStatementSegment(BaseSegment):
    """An `INSERT` statement.

    Redshift has two versions of insert statements:
        - https://docs.aws.amazon.com/redshift/latest/dg/r_INSERT_30.html
        - https://docs.aws.amazon.com/redshift/latest/dg/r_INSERT_external_table.html
    """

    # TODO: This logic can be streamlined. However, there are some odd parsing issues.
    # See https://github.com/sqlfluff/sqlfluff/pull/1896

    type = "insert_statement"
    match_grammar = Sequence(
        "INSERT",
        "INTO",
        Ref("TableReferenceSegment"),
        OneOf(
            OptionallyBracketed(Ref("SelectableGrammar")),
            Sequence("DEFAULT", "VALUES"),
            Sequence(
                Ref("BracketedColumnReferenceListGrammar", optional=True),
                OneOf(
                    Ref("ValuesClauseSegment"),
                    OptionallyBracketed(Ref("SelectableGrammar")),
                ),
            ),
        ),
    )

@redshift_dialect.segment(replace=True)
class AccessStatementSegment(BaseSegment):
    """A `GRANT` statement.

    As specified in: https://docs.aws.amazon.com/redshift/latest/dg/r_GRANT.html

    """

    type = "access_statement"
    match_grammar = Sequence(
        "GRANT",
        OneOf(
            # Table
            Sequence(
                OneOf(
                    "ALL",
                    AnyNumberOf(
                        "SELECT",
                        "INSERT",
                        "UPDATE",
                        "DELETE",
                        "DROP",
                        "REFERENCES"
                    )
                ),
                Ref.keyword("PRIVILEGES", optional=True),
                "ON",
                OneOf(
                    Sequence(Ref.keyword("TABLE", optional=True), Delimited(Ref("TableReferenceSegment"))),
                    Sequence("ALL", "TABLES", "IN", "SCHEMA", Delimited(Ref("SchemaReferenceSegment")))
                ),
                "TO",
                Delimited(
                    OneOf(  # This might not be needed
                        Sequence(Ref("NakedIdentifierSegment"), Sequence("WITH", "GRANT", "OPTION", optional=True)),
                        Sequence("GROUP", Ref("NakedIdentifierSegment")),
                        "PUBLIC"
                    )
                )
            ),

            # Database
            Sequence(
                OneOf(
                    "ALL",
                    AnyNumberOf(
                        "CREATE",
                        "TEMPORARY",
                        "TEMP"
                    )
                ),
                Ref.keyword("PRIVILEGES", optional=True),
                "ON",
                "DATABASE",
                Delimited(Ref("DatabaseReferenceSegment")),
                "TO",
                Delimited(
                    OneOf(  # This might not be needed
                        Sequence(Ref("NakedIdentifierSegment"), Sequence("WITH", "GRANT", "OPTION", optional=True)),
                        Sequence("GROUP", Ref("NakedIdentifierSegment")),
                        "PUBLIC"
                    )
                )
            ),

            # Schema
            Sequence(
                OneOf(
                    "ALL",
                    AnyNumberOf(
                        "CREATE",
                        "USAGE",
                    )
                ),
                Ref.keyword("PRIVILEGES", optional=True),
                "ON",
                "SCHEMA",
                Delimited(Ref("SchemaReferenceSegment")),
                "TO",
                Delimited(
                    OneOf(  # This might not be needed
                        Sequence(Ref("NakedIdentifierSegment"), Sequence("WITH", "GRANT", "OPTION", optional=True)),
                        Sequence("GROUP", Ref("NakedIdentifierSegment")),
                        "PUBLIC"
                    )
                )
            ),

            # Function/Procedure
            Sequence(
                OneOf(
                    "ALL",
                    "EXECUTE"
                ),
                Ref.keyword("PRIVILEGES", optional=True),
                "ON",
                OneOf(
                    Sequence(OneOf("FUNCTION", "PROCEDURE"), Delimited(Ref("FunctionSegment"))),
                    Sequence("ALL", OneOf("FUNCTIONS", "PROCEDURES"), "IN", "SCHEMA", Delimited(Ref("SchemaReferenceSegment")))
                ),
                "TO",
                Delimited(
                    OneOf(  # This might not be needed
                        Sequence(Ref("NakedIdentifierSegment"), Sequence("WITH", "GRANT", "OPTION", optional=True)),
                        Sequence("GROUP", Ref("NakedIdentifierSegment")),
                        "PUBLIC"
                    )
                )

            ),

            # Language
            Sequence(
                "USAGE",
                "ON",
                "LANGUAGE",
                Delimited("plpythonu", "sql"),
                "TO",
                Delimited(
                    OneOf(  # This might not be needed
                        Sequence(Ref("NakedIdentifierSegment"), Sequence("WITH", "GRANT", "OPTION", optional=True)),
                        Sequence("GROUP", Ref("NakedIdentifierSegment")),
                        "PUBLIC"
                    )
                )
            ),

            # Column-level privileges
            Sequence(
                OneOf(
                    "SELECT",
                    "UPDATE",
                    "ALL"
                ),
                Ref.keyword("PRIVILEGES", optional=True),
                Bracketed(Delimited(Ref("ColumnReferenceSegment"))),
                "ON",
                Ref.keyword("TABLE", optional=True),
                Delimited(Ref("TableReferenceSegment")),
                "TO",
                Delimited(
                    OneOf(  # This might not be needed
                        Ref("NakedIdentifierSegment"),
                        Sequence("GROUP", Ref("NakedIdentifierSegment")),
                        "PUBLIC"
                    )
                )
            ),

            # Assumerole
            Sequence(),

            # Redshift Spectrum
            Sequence()
        )
    )


@redshift_dialect.segment(replace=True)
class InsertStatementSegment(BaseSegment):
    """An`INSERT` statement.

    Redshift has two versions of insert statements:
        - https://docs.aws.amazon.com/redshift/latest/dg/r_INSERT_30.html
        - https://docs.aws.amazon.com/redshift/latest/dg/r_INSERT_external_table.html
    """

    # TODO: This logic can be streamlined. However, there are some odd parsing issues.
    # See https://github.com/sqlfluff/sqlfluff/pull/1896

    type = "insert_statement"
    match_grammar = Sequence(
        "INSERT",
        "INTO",
        Ref("TableReferenceSegment"),
        OneOf(
            OptionallyBracketed(Ref("SelectableGrammar")),
            Sequence("DEFAULT", "VALUES"),
            Sequence(
                Ref("BracketedColumnReferenceListGrammar", optional=True),
                OneOf(
                    Ref("ValuesClauseSegment"),
                    OptionallyBracketed(Ref("SelectableGrammar")),
                ),
            ),
        ),
    )


# Adding Redshift specific statements
@redshift_dialect.segment(replace=True)
class StatementSegment(BaseSegment):
    """A generic segment, to any of its child subsegments."""

    type = "statement"

    parse_grammar = redshift_dialect.get_segment("StatementSegment").parse_grammar.copy(
        insert=[
            Ref("TableAttributeSegment"),
            Ref("ColumnAttributeSegment"),
            Ref("ColumnEncodingSegment"),
            Ref("CreateUserSegment"),
            Ref("CreateGroupSegment"),
            Ref("AlterUserSegment"),
            Ref("AlterGroupSegment"),
        ],
    )

    match_grammar = redshift_dialect.get_segment(
        "StatementSegment"
    ).match_grammar.copy()


@redshift_dialect.segment()
class CreateUserSegment(BaseSegment):
    """`CREATE USER` statement.

    https://docs.aws.amazon.com/redshift/latest/dg/r_CREATE_USER.html
    """

    type = "create_user"

    match_grammar = Sequence(
        "CREATE",
        "USER",
        Ref("NakedIdentifierSegment"),
        Ref.keyword("WITH", optional=True),
        "PASSWORD",
        OneOf(Ref("QuotedLiteralSegment"), "DISABLE"),
        AnyNumberOf(
            OneOf(
                "CREATEDB",
                "NOCREATEDB",
            ),
            OneOf(
                "CREATEUSER",
                "NOCREATEUSER",
            ),
            Sequence(
                "SYSLOG",
                "ACCESS",
                OneOf(
                    "RESTRICTED",
                    "UNRESTRICTED",
                ),
            ),
            Sequence("IN", "GROUP", Delimited(Ref("NakedIdentifierSegment"))),
            Sequence("VALID", "UNTIL", Ref("QuotedLiteralSegment")),
            Sequence(
                "CONNECTION",
                "LIMIT",
                OneOf(
                    Ref("NumericLiteralSegment"),
                    "UNLIMITED",
                ),
            ),
            Sequence(
                "SESSION",
                "TIMEOUT",
                Ref("NumericLiteralSegment"),
            ),
        ),
    )


@redshift_dialect.segment()
class CreateGroupSegment(BaseSegment):
    """`CREATE GROUP` statement.

    https://docs.aws.amazon.com/redshift/latest/dg/r_CREATE_GROUP.html
    """

    type = "create_group"

    match_grammar = Sequence(
        "CREATE",
        "GROUP",
        Ref("NakedIdentifierSegment"),
        Sequence(
            Ref.keyword("WITH", optional=True),
            "USER",
            Delimited(
                Ref("NakedIdentifierSegment"),
            ),
            optional=True,
        ),
    )


@redshift_dialect.segment()
class AlterUserSegment(BaseSegment):
    """`ALTER USER` statement.

    https://docs.aws.amazon.com/redshift/latest/dg/r_ALTER_USER.html
    """

    type = "alter_user"

    match_grammar = Sequence(
        "ALTER",
        "USER",
        Ref("NakedIdentifierSegment"),
        Ref.keyword("WITH", optional=True),
        AnyNumberOf(
            OneOf(
                "CREATEDB",
                "NOCREATEDB",
            ),
            OneOf(
                "CREATEUSER",
                "NOCREATEUSER",
            ),
            Sequence(
                "SYSLOG",
                "ACCESS",
                OneOf(
                    "RESTRICTED",
                    "UNRESTRICTED",
                ),
            ),
            Sequence(
                "PASSWORD",
                OneOf(
                    Ref("QuotedLiteralSegment"),
                    "DISABLE",
                ),
                Sequence("VALID", "UNTIL", Ref("QuotedLiteralSegment"), optional=True),
            ),
            Sequence(
                "RENAME",
                "TO",
                Ref("NakedIdentifierSegment"),
            ),
            Sequence(
                "CONNECTION",
                "LIMIT",
                OneOf(
                    Ref("NumericLiteralSegment"),
                    "UNLIMITED",
                ),
            ),
            OneOf(
                Sequence(
                    "SESSION",
                    "TIMEOUT",
                    Ref("NumericLiteralSegment"),
                ),
                Sequence(
                    "RESET",
                    "SESSION",
                    "TIMEOUT",
                ),
            ),
            OneOf(
                Sequence(
                    "SET",
                    Ref("NakedIdentifierSegment"),
                    OneOf(
                        "TO",
                        Ref("EqualsSegment"),
                    ),
                    OneOf(
                        "DEFAULT",
                        Ref("LiteralGrammar"),
                    ),
                ),
                Sequence(
                    "RESET",
                    Ref("NakedIdentifierSegment"),
                ),
            ),
            min_times=1,
        ),
    )


@redshift_dialect.segment()
class AlterGroupSegment(BaseSegment):
    """`ALTER GROUP` statement.

    https://docs.aws.amazon.com/redshift/latest/dg/r_ALTER_GROUP.html
    """

    type = "alter_group"

    match_grammar = Sequence(
        "ALTER",
        "GROUP",
        Ref("NakedIdentifierSegment"),
        OneOf(
            Sequence(
                OneOf("ADD", "DROP"),
                "USER",
                Delimited(
                    Ref("NakedIdentifierSegment"),
                ),
            ),
            Sequence(
                "RENAME",
                "TO",
                Ref("NakedIdentifierSegment"),
            ),
        ),
    )
