import olx

for page in olx.search("https://ba.olx.com.br/?q=galaxy%20s20", 8).pages:
    print(f"Page: {page.number}")
    for ad in page.ads:
        print(f"{ad.title}: R$ {ad.price}")