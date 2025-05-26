from notion_client import Client

notion = Client(auth="")  # Fill with your real token

page_id = ""  # Fill it with actual Notion page ID

highlights = [
    "Highlight 1: This is an important point.",
    "Highlight 2: this defines the topic",
    "Highlight 3: This is a seful quote or insight."
]

def add_highlights_to_notion(highlights):
    children = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": highlight
                        }
                    }
                ]
            }
        } for highlight in highlights
    ]

    notion.blocks.children.append(
        block_id=page_id,
        children=children
    )

add_highlights_to_notion(highlights)
