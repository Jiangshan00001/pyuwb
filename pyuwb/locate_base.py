

class AnchorLocateBase():
    def __init__(self):
        self.anchor_list=None

    def set_anchor_info(self, anchor_list):
        """
        :param anchor_list:[
        {
            client_id:'1-2-3',
            dist:{'1-2-1':10.5,... },
            direction_point:'N'
        },
        ...
          ]
        :return:
        """

        self.anchor_list = anchor_list

    def calc(self):
        """

        :return:
        """
        pass

    def get_anchor_pos(self):
        """

        :return:{
            client_id:'1-2-3',
            pos:{x:x, y:y, z:z}
        }
        """
        return self.anchor_list



