import asf_search as asf

results = asf.search(
    platform=asf.PLATFORM.SENTINEL1,
    processingLevel=asf.PRODUCT_TYPE.SLC,
    beamMode=asf.BEAMMODE.IW,
    intersectsWith='POLYGON((-69 -33,-67 -33,-67 -31,-69 -31,-69 -33))',
    start='2023-01-01T00:00:00Z',
    end='2023-02-01T00:00:00Z',
    maxResults=10
)

if not results:
    print("No se encontraron imagenes para ese periodo y region.")
else:
    print(f"Se encontraron {len(results)} imagenes:")
    for r in results:
        print(f"  {r.properties['startTime']}  {r.properties['fileName']}")
