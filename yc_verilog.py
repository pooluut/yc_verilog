import sublime, sublime_plugin
import re
import os


re_assignment = r".*<=.*"               # problem in // **** <= ****
re_assign = r".*assign"

def is_sth (pattern,str) :
    m = re.match(pattern, str)
    if m:
        return 1
    else:
        return 0

def str_find (pattern,string,start):
    re_m = re.compile(pattern)
    m = re_m.search (string,start)
    if m:
        return [m.start(),m.end()]
    else:
        return [-1,-1]

class AlignmentYcCommand(sublime_plugin.TextCommand):
    """docstring for VerilogCommand"""
    def run (self, edit):
        view = self.view
        sel = view.sel()
        self.algin_parameter(view,sel,edit)
        self.align_ports(view,sel,edit)
        self.align_def(view,sel,edit)
        self.align_inst(view,sel,edit)
        # self.align_assign(view,sel,edit)
        self.align_sth (view,sel,edit,re_assignment,["[", "(-:)|(\+:)|:", "]", "<=" , "[", ":" , "]" , ";" , "//"])
        self.align_sth (view,sel,edit,re_assign,["assign" , "=" , ";" , "//"])


    def align_sth (self,view,sel,edit,cmdline,chars):
        last_pos = []
        for line_sel in view.lines(sel[0]):
            line_str = view.substr(line_sel)
            if (is_sth(cmdline,line_str)):
                last_pos.append(0)
    
        for char in chars:
            char_pos = []
            line_nums = []
            if char in ["[","(","{",")"]:
                re_char = "\\"+char
            else :
                re_char = char
            for line_sel in view.lines(sel[0]):
                line_str = view.substr(line_sel)
                if (is_sth(cmdline,line_str)):
                    # print ("yes")
                    [dump,max_pos] = str_find("((,|;)\s*$)|((,|;)\s*//)",line_str,0)
                    start_pos = last_pos.pop()
                    [cur_pos,end_pos] = str_find(re_char,line_str,start_pos)
                    # print (re_char,cur_pos,max_pos)
                    # print (re_char,cur_pos,start_pos,max_pos,end_pos)
                    if end_pos>max_pos :
                        end_pos = -1
                    last_pos.insert(0,max(start_pos,end_pos))
                    if max_pos==-1:
                        char_pos.append (cur_pos)
                    elif (cur_pos>max_pos):
                        char_pos.append (-1)
                    else:
                        char_pos.append (cur_pos)
                    line_nums.append (view.rowcol(line_sel.a)[0])
            # print ("last:",last_pos)
            # print (line_nums,char_pos)
            self.insert_operation (view,sel,edit,line_nums,char_pos)


    def align_inst(self,view,sel,edit):
        inst_pattern = r"\s*\.\s*([_A-Za-z0-9]+)\s*\(([_A-Za-z0-9]*)\s*(\),?)((?://)?.*)"
        # inst_pattern = r"\s*\.\s*([_A-Za-z0-9]+)\s*\(\s*([_A-Za-z0-9]+)(\),?)((?://)?[/ \.:;\+\*-,_A-Za-z0-9]*)"
        port_list = self.get_list(view,sel,inst_pattern,4)
        print(port_list)
        if port_list :
            lines = view.lines(sel[0])
            lines.reverse()
            max_0 = max([len(x[0]) for x in port_list])
            max_1 = max([len(x[1]) for x in port_list])
            max_3 = max([len(x[3]) for x in port_list])
            for line_sel in lines :
                line_str = view.substr(line_sel)
                m = re.match ("\s*\.", line_str)
                if m :
                    rep_ls = port_list.pop()
                    rep_line = "        ."+rep_ls[0]+" "*(max_0-len(rep_ls[0])) + " ("
                    if len(rep_ls[1]) :
                        rep_line += rep_ls[1] + " "*(max_1-len(rep_ls[1]))
                    if len(rep_ls[2])==1 :
                        rep_line += ") "
                    else :
                        rep_line += "),"
                    if len(rep_ls[3]) :
                        rep_line += " " +rep_ls[3]
                    # print (rep_line)
                    view.replace(edit,line_sel,rep_line)


    def align_def(self,view,sel,edit):
        def_pattern = r"\s*(reg|wire)\s+(?:\[\s*([-\*\+_A-Z0-9]*)\s*:\s*([-\*\+_A-Z0-9]*)\s*\])?\s*([_A-Za-z0-9]+)\s*([,;]?)\s*((?://)?.*)"
        port_list1 = self.get_list(view,sel,def_pattern,6) 
        port_list = []
        for each_port in port_list1 :
            port_list.append(["" if x==None else x for x in each_port])
        # print(port_list)
        if port_list :
            lines = view.lines(sel[0])
            lines.reverse()
            max_0 = max([len(x[0]) for x in port_list])
            max_1 = max([len(x[1]) for x in port_list])
            max_2 = max([len(x[2]) for x in port_list])
            max_3 = max([len(x[3]) for x in port_list])
            for line_sel in lines :
                line_str = view.substr(line_sel)
                m = re.match ("\s*(reg|wire)", line_str)
                if m :
                    rep_ls = port_list.pop()
                    rep_line = "    "+rep_ls[0]+" "*(max_0-len(rep_ls[0])) + " "
                    if len(rep_ls[1]) :
                        rep_line += "[" + " "*(max_1-len(rep_ls[1])) + rep_ls[1] + ":" + rep_ls[2] + " "*(max_2-len(rep_ls[2])) + "]"
                    else :
                        rep_line += " "*(max_1+max_2+3)
                    rep_line += " " + rep_ls[3] + " "*(max_3-len(rep_ls[3])+1)
                    if len(rep_ls[4]) :
                        rep_line += rep_ls[4]
                    else :
                        rep_line += " "
                    if len(rep_ls[5]) :
                        rep_line += " " + rep_ls[5]
                    # print (rep_line)
                    view.replace(edit,line_sel,rep_line)


    def algin_parameter(self,view,sel,edit):
        para_pattern = r"\s*parameter\s+([_A-Z0-9]+)\s*=\s*(['A-Za-z0-9_]*)\s*(,?)\s*((?://)?.*)"
        para_list = self.get_list(view,sel,para_pattern,4)
        # print(para_list)
        if para_list :
            lines = view.lines(sel[0])
            lines.reverse()
            max_1 = max([len(x[0]) for x in para_list])
            # print (max_1)
            max_2 = max([len(x[1]) for x in para_list])
            for line_sel in lines :
                line_str = view.substr(line_sel)
                m = re.match ("\s*parameter", line_str)
                if m :
                    rep_ls = para_list.pop()
                    rep_line = "    parameter " + rep_ls[0] + " "*(max_1-len(rep_ls[0])) + " = " + rep_ls[1] + " "*(max_2-len(rep_ls[1]))
                    if len(rep_ls[2]) :
                        rep_line += " ,"
                    else :
                        rep_line += "  "
                    if len(rep_ls[3]) :
                        rep_line += " " + rep_ls[3]
                    # print (rep_line)
                    view.replace(edit,line_sel,rep_line)


    def align_ports(self,view,sel,edit):
        port_pattern = r"\s*(output\s+reg|input|output)\s+(?:\[\s*([-\*\+_A-Z0-9]*)\s*:\s*([-\*\+_A-Z0-9]*)\s*\])?\s*([_A-Za-z0-9]+)\s*([,;]?)\s*((?://)?.*)"
        port_list1 = self.get_list(view,sel,port_pattern,6) 
        port_list = []
        for each_port in port_list1 :
            port_list.append(["" if x==None else x for x in each_port])
        # print(port_list)
        if port_list :
            lines = view.lines(sel[0])
            lines.reverse()
            max_0 = max([len(x[0]) for x in port_list])
            max_1 = max([len(x[1]) for x in port_list])
            max_2 = max([len(x[2]) for x in port_list])
            max_3 = max([len(x[3]) for x in port_list])
            last = 1
            for line_sel in lines :
                line_str = view.substr(line_sel)
                m = re.match ("\s*(input|output|output\s+reg)", line_str)
                if m :
                    rep_ls = port_list.pop()
                    rep_line = "    "+rep_ls[0]+" "*(max_0-len(rep_ls[0])) + " "
                    if len(rep_ls[1]) :
                        rep_line += "[" + " "*(max_1-len(rep_ls[1])) + rep_ls[1] + ":" + rep_ls[2] + " "*(max_2-len(rep_ls[2])) + "]"
                    else :
                        rep_line += " "*(max_1+max_2+3)
                    rep_line += " " + rep_ls[3] + " "*(max_3-len(rep_ls[3])+1)
                    if last==1 :
                        rep_line += " "
                        last = 0
                    else :
                        rep_line += ","
                    if len(rep_ls[5]) :
                        rep_line += " " + rep_ls[5]
                    # print (rep_line)
                    view.replace(edit,line_sel,rep_line)


    def get_list(self,view,sel,pattern,num) :
        return_list = []
        for line_sel in view.lines(sel[0]):
            line_str = view.substr(line_sel)
            m = re.match (pattern, line_str)
            if m:
                return_list.append([m.group(i) for i in range(1,num+1)])
                # return_list.append((m.group(1),m.group(2),m.group(3),m.group(4),m.group(5),m.group(6)))
        return return_list



    def insert_operation (self,view,sel,edit,line_nums,char_pos):
        for i in range(len(line_nums)) :
            pt = view.text_point(line_nums[i],char_pos[i])
            if char_pos[i]>=0 :
                view.insert (edit, pt, ' '*(max(char_pos)-char_pos[i]))





class AutoInstYcCommand(sublime_plugin.TextCommand):
    """docstring for AutoInstYcCommand"""
    def run (self, edit) :
        view = self.view
        sel = view.sel()
        cur_point = sel[0].a
        cur_word_sel = view.word(cur_point)
        cur_word = view.substr(cur_word_sel)
        # print (cur_word_sel,cur_word)
        if cur_word=="module":
            end_module_sel=view.find("\);",cur_word_sel.b)
            # print(view.substr(result))
            module_sel=cur_word_sel.cover(end_module_sel)
            # print (view.substr(module_sel))
            module_pattern = r"\s*module\s+([A-Za-z0-9_]*)" 
            input_pattern = r"\s*\binput\b\s*(?:signed)*\s*(\[[ A-Z0-9_\*-:\+]*\])*\s+([A-Za-z0-9_]*)\s*,*\s*(?://)*"
            output_pattern = r"\s*\boutput\b\s*(?:reg)*\s*(\[[ A-Z0-9_\*-:\+]*\])*\s+([A-Za-z0-9_]*)\s*,*\s*(?://)*"
            module_name = self.get_list(view,module_sel,module_pattern,1)[0]
            # print (module_name)
            input_list = self.get_list(view,module_sel,input_pattern,2)
            output_list = self.get_list(view,module_sel,output_pattern,2)
            print (output_list)
            self.insert_operations (view,edit,cur_word_sel.a,module_name,input_list,output_list)


    def get_list(self,view,module_sel,pattern,num) :
        return_list = []
        for line_sel in view.lines(module_sel):
            line_str = view.substr(line_sel)
            m = re.match (pattern, line_str)
            if m :
                if num==1 :
                    return_list.append( m.group(1) )
                elif num==2 :
                    return_list.append( (m.group(1), m.group(2) ) )
                elif num==3 :
                    return_list.append( (m.group(1), m.group(2), m.group(3) ) )
        return return_list 


    def insert_operations (self,view,edit,insert_point,module_name,input_list,output_list) :
        input_line = ""
        output_line = ""
        cnt = 0 
        output_num = len(output_list)
        for each_input_line in input_list :
            input_line += "    ." + each_input_line[1] + "(" + each_input_line[1] + "),"
            if each_input_line[0] :
                input_line += "// " + each_input_line[0]
            input_line += "\n"
        for each_output_line in output_list:
            cnt = cnt + 1
            output_line += "    ." + each_output_line[1] + "(" + each_output_line[1] + "),"
            if cnt==output_num :
                output_line = output_line[:-1]
            if each_output_line[0] :
                output_line += "// " + each_output_line[0]
            output_line += "\n"
        print(output_line)
        inst = module_name + " u_" + module_name + " (" + "\n" + input_line + output_line + ");\n"
        sublime.set_clipboard(inst)
        # view.insert(edit,insert_point,inst)



class GoToDefinitionYcCommand(sublime_plugin.WindowCommand):
    """docstring for GoToDefinitionCommand"""
    def run (self) :
        window = self.window
        view = window.active_view()
        sel = view.sel()
        cur_point = sel[0].a
        cur_word_sel = view.word(cur_point)
        cur_word = view.substr(cur_word_sel)
        def_pattern = r"\s*(input|parameter|output|reg|wire)\s*(reg|signed)*\s+(\[[ A-Za-z0-9_\*-:\+]*\])*\s*([A-Za-z0-9_]*\s*,\s*)*"+cur_word
        def_region=view.find(def_pattern,0)
        line = view.rowcol(def_region.b)[0]
        print(line)
        if line:
            view.run_command("goto_line",{"line": line+1})
        else :
            window.run_command("show_overlay",{"overlay": "goto", "show_files": 1, "text":cur_word})




class AutoDefYcCommand(sublime_plugin.TextCommand):
    """docstring for AutoDefYcCommand"""
    def run (self, edit):
        view = self.view
        sel = view.sel()
        cur_point = sel[0].a
        cur_word_sel = view.word(cur_point)
        cur_line_sel = view.line(cur_point)
        cur_line_str = view.substr(cur_line_sel)
        cur_word = view.substr(cur_word_sel)
        if (cur_word=="module" or re.match("\s*module\s+"+cur_word,cur_line_str)) :
            self.def_port(view,edit,cur_word_sel)
        else :
            self.def_signal(view,edit,cur_word)

    def def_signal (self,view,edit,cur_word):
        def_pattern = r"\s*(//)?\s*(input|parameter|output|reg|wire)\s+(reg|signed)*\s*(\[[ A-Z0-9_\*-:\+]*\])*\s*([A-Za-z0-9_]*\s*,\s*)*"+cur_word
        def_region=view.find(def_pattern,0)
        cur_line = view.rowcol(def_region.b)[0]
        print(cur_line)
        if (cur_line==0) :
            if re.match("i_",cur_word) :
                insert_pattern = r"\);" 
                insert_region = view.find(insert_pattern,0)
                insert_point = view.line(insert_region.a-1).a
                view.insert(edit, insert_point, "    // input    "+cur_word+" ,\n")
            elif re.match("o_",cur_word) :
                insert_pattern = r"\);" 
                insert_region = view.find(insert_pattern,0)
                insert_point = view.line(insert_region.a-1).a
                view.insert(edit, insert_point, "    // output    "+cur_word+" ,\n")
            else:
                insert_pattern = r"\s*//\s*MAIN_CODE"
                insert_region = view.find(insert_pattern,0)
                insert_point = view.text_point(view.rowcol(insert_region.a)[0]-1,0)
                view.insert(edit, insert_point, "    // reg    "+cur_word+" ;\n")
        else :
            print (cur_line)
            def_reg_pattern = r"\s*reg\s*"+cur_word
            def_wire_pattern = r"\s*wire\s*"+cur_word
            def_reg_region = view.find(def_reg_pattern,0)
            def_wire_region = view.find(def_wire_pattern,0)
            print (def_reg_region)
            print (def_wire_region)
            if def_reg_region.a!=-1 :
                view.replace(edit,view.line(def_reg_region),"    // wire    "+cur_word+" ;")
            elif def_wire_region.a!= -1 :
                view.replace(edit,view.line(def_wire_region),"    // reg    "+cur_word+" ;")




    def def_port (self,view,edit,cur_word_sel):
        end_module_sel=view.find("\);",cur_word_sel.b)
        # print (end_module_sel)
        module_sel=cur_word_sel.cover(end_module_sel)
        para_pattern = r"\s*parameter\s+([_A-Z0-9]+)\s*=\s*(['-\*\+A-Za-z0-9_]*)\s*,?\s*((?://)?.*)"
        input_pattern = r"\s*\binput\b\s*(?:signed)*\s*(\[[ A-Z0-9_\*-:\+]*\])*\s+([A-Za-z0-9_]*)\s*[,(?://)]?"
        output_pattern = r"\s*\boutput\b\s*(?:reg)*\s*(\[[ A-Z0-9_\*-:\+]*\])*\s+([A-Za-z0-9_]*)\s*[,(?://)]?"
        para_list = self.get_list(view,module_sel,para_pattern,2)
        input_list = self.get_list(view,module_sel,input_pattern,2)
        output_list = self.get_list(view,module_sel,output_pattern,2)
        # print (para_list)
        # print (input_list)
        # print (output_list)
        self.insert_operations (para_list,input_list,output_list)

    def get_list(self,view,module_sel,pattern,num) :
        return_list = []
        for line_sel in view.lines(module_sel):
            line_str = view.substr(line_sel)
            m = re.match (pattern, line_str)
            if m :
                if num==1 :
                    return_list.append( m.group(1) )
                elif num==2 :
                    return_list.append( (m.group(1), m.group(2) ) )
                elif num==3 :
                    return_list.append( (m.group(1), m.group(2), m.group(3) ) )
        return return_list 

    def insert_operations (self,para_list,input_list,output_list) :
        para_line = ""
        input_line = ""
        output_line = ""
        for each_para_line in para_list :
            para_line += "parameter " + each_para_line[0] + " = " + each_para_line[1] + " ;\n"
        for each_input_line in input_list :
            if each_input_line[0] :
                input_line += "reg " + each_input_line[0] + " " + each_input_line[1] + " ;\n"
            else :
                input_line += "reg " + each_input_line[1] + " ;\n"
        for each_output_line in output_list :
            if each_output_line[0] :
                output_line += "wire " + each_output_line[0] + " " + each_output_line[1] + " ;\n"
            else :
                output_line += "wire " + each_output_line[1] + " ;\n"
        inst = para_line + "\n" + input_line + "\n" + output_line + "\n"
        sublime.set_clipboard(inst)






        

class AutoSplitYcCommand(sublime_plugin.TextCommand):
    """docstring for AutoSplitYcCommand"""
    def run (self, edit) :
        view = self.view
        sel = view.sel()
        cur_point = sel[0].a
        cur_line_sel = view.line(cur_point)
        cur_line_str = view.substr(cur_line_sel)
        def_pattern = r"\s*(?:input|output|reg)\s+(?:reg)*\[(\d+)\*([ A-Z0-9_\*-:\+]+)\]\s+([A-Za-z0-9_]*)\s*[,;]*\s*(?://)*"
        m = re.match (def_pattern,cur_line_str)
        if m :
            num = int(m.group(1))
            new_num = str(num-1)
            insert_str = "    wire [" + m.group(2) + "] " + m.group(3) + "_s [" + new_num + ":0];\n"
            b = [m.group(3)+"_s["+str(num-i-1)+"]" for i in range(num)]
            a = ",".join(b)
            insert_str += "    assign {" + a + "} = " + m.group(3) + " ;\n\n"
            insert_pattern = r"    //                 END_SPLIT" 
            insert_region = view.find(insert_pattern,0)
            insert_point = insert_region.a
            view.insert (edit,insert_point,insert_str)







class PlotWaveYcCommand(sublime_plugin.TextCommand):
    def run (self, edit) :
        view = self.view
        # insert_point = view.sel()[0].a
        # print(sel)
        file_region = sublime.Region(0,view.size())
        lines = view.lines(file_region)
        # self.pre_process(view,edit,lines) 
        self.pre_process_new(view,edit,lines) 
        
        view = self.view
        file_region = sublime.Region(0,view.size())
        lines = view.lines(file_region)
        insert_str = self.parse_lines_2 (view,edit,lines)
        replace_region = self.find_replace_region(view)
        self.replace_operation(view,edit,replace_region,insert_str[:-1])

    def replace_operation(self,view,edit,replace_region,insert_str):
        view.replace(edit,replace_region,insert_str)

    def pre_process_new(self,view,edit,lines):
        lines.reverse()
        for each_line_sel in lines :
            line_str = view.substr(each_line_sel)
            sig_pattern = r"(//\s*[A-Za-z0-9_]+\s*`)([-~_\|]*)\"([-~_\|]*)\"\s*\*([0-9]+)"
            bus_pattern = r"(//\s*[A-Za-z0-9_]+\s*`)([^\"]*)\"([^\"]*)\"\*([0-9]+),([0-9]+)-([0-9]+)"
            m1 = re.match(sig_pattern,line_str)
            m2 = re.match(bus_pattern,line_str)
            if m1 :
                name = m1.group(1)
                pre_signal = m1.group(2)
                signal = m1.group(3)
                num = int(m1.group(4))
                insert_str = name + pre_signal + signal*num
                view.replace(edit,each_line_sel,insert_str)
            elif m2 :
                name = m2.group(1)
                pre_signal = m2.group(2)
                signal = m2.group(3)
                cycle = int(m2.group(4))
                start_num = int(m2.group(5))
                end_num = int(m2.group(6))
                print (signal)
                m_lable = re.match(r"([\| ]*)(\w*)(\$?)([\| ]*)",signal)
                signal1 = m_lable.group(1)
                lable=m_lable.group(2)
                if m_lable.group(3) :
                    is_dollar = 1
                else :
                    is_dollar = 0 
                signal2 = m_lable.group(4)

                data_srt=""
                num = start_num
                for i in range(0,cycle) :
                    data_srt += signal1 + lable
                    if is_dollar :
                        data_srt += str(num) + signal2[len(str(num))-1:]
                    else :
                        data_str += signal2 
                    num = ( num + 1 ) % (end_num-start_num+1)
                # print (data_srt)
                insert_str = name + pre_signal + data_srt

                view.replace(edit,each_line_sel,insert_str)

    def pre_process(self,view,edit,lines):
        lines.reverse()
        for each_line_sel in lines :
            line_str = view.substr(each_line_sel)
            clk_pattern_1 = r"// `[cs] ([A-Za-z0-9_]+) ([0-9]+) ([0-9]+) ([0-9]+)"
            clk_pattern_2 = r"// `[cs] ([A-Za-z0-9_]+) ([0-9]+) ([0-9]+)"
            bus_pattern = r"// `b ([A-Za-z0-9_]+) ([A-Za-z0-9_]+) ([0-9]+)-([0-9]+) ([0-9]+) ([0-9]+)"
            m1 = re.match(clk_pattern_1,line_str)
            m2 = re.match(clk_pattern_2,line_str)
            m3 = re.match(bus_pattern,line_str)
            if m1 :
                name = m1.group(1)
                high = int(m1.group(2))
                low = int(m1.group(3))
                cycle = int(m1.group(4))
                print (high,low, cycle)
                insert_str = self.get_ins_str_signal(view,name,high,low,cycle)
                view.replace(edit,each_line_sel,insert_str)
            elif m2 :
                name = m2.group(1)
                high = int(m2.group(2))
                cycle = int(m2.group(3))
                low = high 
                print (high,low, cycle)
                insert_str = self.get_ins_str_signal(view,name,high,low,cycle)
                view.replace(edit,each_line_sel,insert_str)
            elif m3 :
                name = m3.group(1)
                lable = m3.group(2)
                start_num = int(m3.group(3))
                end_num = int(m3.group(4))
                width = int(m3.group(5))
                cycle = int(m3.group(6))
                print (start_num,end_num,width,cycle)
                insert_str = self.get_ins_str_bus (view,name,lable,start_num,end_num,width,cycle)
                view.replace(edit,each_line_sel,insert_str)

    def get_ins_str_bus (self,view,name,lable,start_num,end_num,width,cycle):
        space_len = int((width-1-len(lable))/2)
        data_srt = ""
        num = start_num
        for i in range(0,cycle) :
            cur_data_srt = " "*space_len+lable+str(num)
            num = ( num + 1 ) % (end_num-start_num+1)
            left_len = width - len (cur_data_srt)
            cur_data_srt += " "*left_len
            data_srt += cur_data_srt + "|"
        # print (data_srt)
        insert_str = "// " + name + " ` |" + data_srt
        # print (insert_str)
        return insert_str

    def get_ins_str_signal (self,view,name,high,low,cycle):
        insert_str = "// " + name + " `_|" + (("-"*high+"|") + ("_"*low+"|"))*cycle 
        # print (insert_str)
        return insert_str

    def find_replace_region(self,view):
        wave_pattern = r"\s*//                 WAVE"
        wave_start_point = view.find(wave_pattern,0).b
        wave_end_point = view.find(r"\s*//================================",wave_start_point).a
        # print (wave_start_point)
        return sublime.Region(wave_start_point,wave_end_point)

    def parse_lines_2 (self,view,edit,lines) :
        signal_name = []
        signal_wave = []
        for each_line_sel in lines :
            line_str = view.substr(each_line_sel)
            if (line_str.startswith("//")):
                if (line_str.find("`")!=-1) :
                    signal_name.append(line_str.split("`")[0])
                    signal_wave.insert(0,line_str.split("`")[1])
                    # print (signal_name)
                    # print (signal_wave)
        len_name = max([len(i) for i in signal_name])
        len_wave = max([len(i) for i in signal_wave])
        # print (len_name)
        # print (len_wave)
        insert_str = "\n"
        for each_name in signal_name :
            line_1 = "//" + " " * (len_name-2) + "│ "
            line_2 = each_name + " "*(len_name-len(each_name)) +"│ "
            line_3 = "//" + " " * (len_name-2) + "│ "
            # print (line_1)
            # print (line_2)
            # print (line_3)
            line = signal_wave.pop()
            if (line[0]=='-' or line[0] == '_') :
                is_bus = 0
            elif (line[0]=='='):
                is_bus = 5
            else :
                is_bus = 1

            if is_bus :
                for word in line :
                    if (word == '|') :
                        line_1 += '┬'
                        line_2 += '│'
                        line_3 += '┴'
                    elif (word == '~') :
                        line_1 += '/'
                        line_2 += '~'
                        line_3 += '/'
                    else :
                        line_1 += '─'
                        line_2 += word
                        line_3 += '─'
            else :
                rst = 0 
                if (line[0] == '-') :
                    fc = 1 
                elif (line[0] == '_'):
                    fc = 0 
                
                for word in line :
                    if rst == 1 :
                        if (word == '-') :
                            fc = 1 
                        elif (word == '_'):
                            fc = 0 

                    if ( word == '-'):
                        line_1 += '─'
                        line_2 += ' '
                        line_3 += ' '
                    elif (word == '_'):
                        line_1 += ' '
                        line_2 += ' '
                        line_3 += '─'
                    elif (word == '|'):
                        line_2 += "│"
                        if(fc==0):
                            fc=1 
                            line_1 += '┌'
                            line_3 += "┘"
                        else :
                            fc=0 
                            line_1 += '┐'
                            line_3 += "└"
                    elif (word == '~') :
                        rst = 1 
                        line_1 += ' '
                        line_2 += '~'
                        line_3 += ' '

            line_1 += '\n'
            line_2 += '\n'
            line_3 += '\n'
            if is_bus==5 :
                insert_str += each_name + " "*(len_name-len(each_name)) + "│=" + line
            else :
                insert_str += line_1+line_2+line_3
        # insert_str += "/" * (len_name+len_wave+4) + "\n"
        # print (insert_str)
        return insert_str

        # view.insert(edit,view.sel()[0].a,insert_str)





