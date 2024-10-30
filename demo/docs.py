_docs = {
    "WebRTC": {
        "description": "Stream audio/video with WebRTC",
        "members": {
            "__init__": {
                "rtc_configuration": {
                    "type": "dict[str, Any] | None",
                    "default": "None",
                    "description": "The configration dictionary to pass to the RTCPeerConnection constructor. If None, the default configuration is used.",
                },
                "height": {
                    "type": "int | str | None",
                    "default": "None",
                    "description": "The height of the component, specified in pixels if a number is passed, or in CSS units if a string is passed. This has no effect on the preprocessed video file, but will affect the displayed video.",
                },
                "width": {
                    "type": "int | str | None",
                    "default": "None",
                    "description": "The width of the component, specified in pixels if a number is passed, or in CSS units if a string is passed. This has no effect on the preprocessed video file, but will affect the displayed video.",
                },
                "label": {
                    "type": "str | None",
                    "default": "None",
                    "description": "the label for this component. Appears above the component and is also used as the header if there are a table of examples for this component. If None and used in a `gr.Interface`, the label will be the name of the parameter this component is assigned to.",
                },
                "show_label": {
                    "type": "bool | None",
                    "default": "None",
                    "description": "if True, will display label.",
                },
                "container": {
                    "type": "bool",
                    "default": "True",
                    "description": "if True, will place the component in a container - providing some extra padding around the border.",
                },
                "scale": {
                    "type": "int | None",
                    "default": "None",
                    "description": "relative size compared to adjacent Components. For example if Components A and B are in a Row, and A has scale=2, and B has scale=1, A will be twice as wide as B. Should be an integer. scale applies in Rows, and to top-level Components in Blocks where fill_height=True.",
                },
                "min_width": {
                    "type": "int",
                    "default": "160",
                    "description": "minimum pixel width, will wrap if not sufficient screen space to satisfy this value. If a certain scale value results in this Component being narrower than min_width, the min_width parameter will be respected first.",
                },
                "interactive": {
                    "type": "bool | None",
                    "default": "None",
                    "description": "if True, will allow users to upload a video; if False, can only be used to display videos. If not provided, this is inferred based on whether the component is used as an input or output.",
                },
                "visible": {
                    "type": "bool",
                    "default": "True",
                    "description": "if False, component will be hidden.",
                },
                "elem_id": {
                    "type": "str | None",
                    "default": "None",
                    "description": "an optional string that is assigned as the id of this component in the HTML DOM. Can be used for targeting CSS styles.",
                },
                "elem_classes": {
                    "type": "list[str] | str | None",
                    "default": "None",
                    "description": "an optional list of strings that are assigned as the classes of this component in the HTML DOM. Can be used for targeting CSS styles.",
                },
                "render": {
                    "type": "bool",
                    "default": "True",
                    "description": "if False, component will not render be rendered in the Blocks context. Should be used if the intention is to assign event listeners now but render the component later.",
                },
                "key": {
                    "type": "int | str | None",
                    "default": "None",
                    "description": "if assigned, will be used to assume identity across a re-render. Components that have the same key across a re-render will have their value preserved.",
                },
                "mirror_webcam": {
                    "type": "bool",
                    "default": "True",
                    "description": "if True webcam will be mirrored. Default is True.",
                },
                "postprocess": {
                    "value": {
                        "type": "typing.Any",
                        "description": "Expects a {str} or {pathlib.Path} filepath to a video which is displayed, or a {Tuple[str | pathlib.Path, str | pathlib.Path | None]} where the first element is a filepath to a video and the second element is an optional filepath to a subtitle file.",
                    }
                },
                "preprocess": {
                    "return": {
                        "type": "str",
                        "description": "Passes the uploaded video as a `str` filepath or URL whose extension can be modified by `format`.",
                    },
                    "value": None,
                },
            },
            "events": {"tick": {"type": None, "default": None, "description": ""}},
        },
        "__meta__": {"additional_interfaces": {}, "user_fn_refs": {"WebRTC": []}},
    }
}
