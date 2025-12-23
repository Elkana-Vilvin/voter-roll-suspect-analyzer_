def select_scope_cli(args):
    """
    Determine analysis scope from CLI arguments or interactive input.

    CURRENT SUPPORT:
      - Assembly
      - Booth / Part

    NOTE:
      - State scope is intentionally DISABLED until state_code column
        is officially present in the CSV.
    """

    # -------------------------------
    # CLI MODE
    # -------------------------------
    if args.scope:
        scope = args.scope.lower()

        if scope == "assembly":
            if not args.assembly:
                raise ValueError("Assembly scope requires --assembly")
            return "assembly", args.assembly, None

        if scope == "booth":
            if not args.assembly or not args.booth:
                raise ValueError(
                    "Booth scope requires both --assembly and --booth"
                )
            return "booth", args.assembly, args.booth

        raise ValueError("Unsupported scope (state disabled for now)")

    # -------------------------------
    # INTERACTIVE MODE
    # -------------------------------
    print("\nSelect analysis scope:")
    print("1. Assembly")
    print("2. Booth / Part")

    choice = input("Enter choice (1/2): ").strip()

    if choice == "1":
        assembly = input("Enter assembly number: ").strip()
        return "assembly", assembly, None

    if choice == "2":
        assembly = input("Enter assembly number: ").strip()
        booth = input("Enter part / booth number: ").strip()
        return "booth", assembly, booth

    raise ValueError("Invalid scope selection")
