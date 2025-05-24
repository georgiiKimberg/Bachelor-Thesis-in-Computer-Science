import re
from django.db import connection
class Sequence:
    def __init__(self, sekvens, family, sek_id):
        self.sekvens = sekvens
        self.family = family
        self.sek_id = sek_id
        self.pos_dict = self.get_positions_dict()
        
    
    def get_positions_dict(self):
        pos_dict = {}
        seq = list(map(int, re.findall(r"\d+", self.sekvens)))
        for i, number in enumerate(seq, start=1):  
            if number not in pos_dict:
                pos_dict[number] = []
            pos_dict[number].append(i)
        return pos_dict


    def get_params(self):    
        cursor = connection.cursor()
        cursor.execute(
            'SELECT n_param, a_param, family FROM Sekvenser_params WHERE sek_id = %s',
            (self.sek_id,)
        )
        rows = cursor.fetchall() 

        result = [list(row) for row in rows]
        return result
 



