def printCURocket(rocket_name, version, author):
    print(fr"""
           ^
          / \
         /___\
        |=   =|              |\___/|
        |     |             /       \
        | C U |             |    /\__/|
        | I N |             ||\  <.><.>
        |Space|             | _     > )
        |     |             \   /----
        |     |              |   -\/
       /|##!##|\             /     \
      / |##!##| \
     /  |##!##|  \
    |  / ^ | ^ \  |
    | /  ( | )  \ |
    |/   ( | )   \|
        ((   ))
       ((  :  ))            CU InSpace Avionics Ground Station
       ((  :  ))            {f"Rocket": <11}{rocket_name}
        ((   ))             {f"Version": <11}{version}
          ( )               {f"Author": <11}{author}
              """)