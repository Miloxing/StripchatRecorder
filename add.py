import sys

with open("wanted.txt","a") as f:
    for i in sys.argv[1:]:
        for j in i.split(','):
            j = j.strip()
            ii = 0
            for line in open("wanted.txt").read().splitlines():
                if(line == j):
                    ii =1
                    break
            if(ii == 1):
                print("%s已存在，跳过" % j)
                continue
            f.writelines(j)
            f.write('\n')
            f.close
            print('%s添加成功' % j)
