public class Test {

    public Parser skipString()
    {
       getString();
       return this;
    }
   /** Gets a continuous string of char and go to the next char */
   public String getString()
   {  int begin=index;
      while (begin<str.length() && !isChar(str.charAt(begin))) begin++;
      int end=begin;
      while (end<str.length() && isChar(str.charAt(end))) end++;
      index=end;
      return str.substring(begin,end);
   } 
}
